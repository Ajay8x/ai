"""
AJAX AI - Knowledge Vector Store & RAG Pipeline
Fast local document indexing and semantic retrieval.
"""

import os
import re
import math
import hashlib
from typing import List, Dict, Any, Tuple
from ai.rag.loader import doc_loader
from database.db import is_mongo_active, get_mongo_db, SYSTEM_SCOPE
from core.logger import ajax_logger
from config.config_loader import config

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())


class EmbeddingProvider:
    """Optional multilingual embeddings with a dependency-free fallback.

    If sentence-transformers is installed and explicitly selected, the configured
    multilingual model is used. Otherwise a normalized character/word n-gram
    vector keeps spelling variants and Hinglish retrieval useful without adding a
    heavyweight dependency to Vercel builds.
    """

    DIMENSION = 384

    def __init__(self):
        self.provider = str(getattr(config, "rag_embedding_provider", "auto") or "auto").lower()
        self.model_name = str(getattr(config, "rag_embedding_model", "paraphrase-multilingual-MiniLM-L12-v2"))
        self._model = None
        self._model_checked = False

    def _load_model(self):
        if self._model_checked:
            return self._model
        self._model_checked = True
        # "auto" deliberately stays dependency-free so a serverless cold start
        # never downloads a multi-hundred-MB model unexpectedly.
        if self.provider not in {"sentence_transformers", "sentence-transformers"}:
            return None
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            ajax_logger.info(f"RAG multilingual embedding model loaded: {self.model_name}")
        except Exception as e:
            if self.provider != "auto":
                ajax_logger.warning(f"RAG embedding model unavailable; using local fallback: {e}")
        return self._model

    def embed(self, text: str) -> List[float]:
        normalized = " ".join(str(text or "").lower().split())
        model = self._load_model()
        if model is not None:
            try:
                vector = model.encode(normalized, normalize_embeddings=True).tolist()
                return [float(value) for value in vector]
            except Exception as e:
                ajax_logger.warning(f"RAG embedding inference fallback: {e}")

        vector = [0.0] * self.DIMENSION
        features = tokenize(normalized)
        compact = re.sub(r"\s+", " ", normalized)
        features.extend(compact[index:index + 3] for index in range(max(0, len(compact) - 2)))
        for feature in features:
            digest = hashlib.blake2b(str(feature).encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest, "big") % self.DIMENSION
            vector[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    @staticmethod
    def cosine(left: List[float], right: List[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        return sum(a * b for a, b in zip(left, right))

class RAGStore:
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self._initialized = False
        self.embedding_provider = EmbeddingProvider()

    @staticmethod
    def _source_key(source: Any) -> str:
        source_text = str(source or "")
        if not source_text or source_text == "mongodb_cloud":
            return source_text
        return os.path.normcase(os.path.abspath(source_text))

    def _remove_source_from_memory(self, source: str, user_id: str = SYSTEM_SCOPE) -> int:
        source_key = self._source_key(source)
        before = len(self.documents)
        self.documents = [
            doc for doc in self.documents
            if not (self._source_key(doc.get("source")) == source_key and doc.get("user_id", SYSTEM_SCOPE) == user_id)
        ]
        return before - len(self.documents)

    def _remove_source_from_mongo(self, source: str, user_id: str = SYSTEM_SCOPE):
        if not is_mongo_active():
            return
        try:
            get_mongo_db().rag_documents.delete_many({"source": source, "user_id": user_id})
        except Exception as e:
            ajax_logger.warning(f"Failed removing old RAG chunks from MongoDB: {e}")

    def _ensure_initialized(self):
        if self._initialized:
            return
        self._initialized = True
        
        # 1. Load documents from MongoDB Atlas if active
        if is_mongo_active():
            try:
                db = get_mongo_db()
                mongo_docs = list(db.rag_documents.find({}, {"_id": 0}))
                for doc in mongo_docs:
                    chunk = doc.get("chunk", "")
                    self.documents.append({
                        "id": doc.get("id"),
                        "source": doc.get("source", "mongodb_cloud"),
                        "title": doc.get("title", "Cloud Document"),
                        "file_name": doc.get("file_name", os.path.basename(doc.get("source", ""))),
                        "chunk": chunk,
                        "chunk_index": doc.get("chunk_index", 0),
                        "total_chunks": doc.get("total_chunks", 1),
                        "tokens": set(tokenize(chunk)),
                        "embedding": doc.get("embedding") or self.embedding_provider.embed(chunk),
                        "user_id": doc.get("user_id", SYSTEM_SCOPE)
                    })
                if mongo_docs:
                    ajax_logger.info(f"Loaded {len(mongo_docs)} RAG document chunks from MongoDB Atlas.")
            except Exception as e:
                ajax_logger.warning(f"Failed loading RAG docs from MongoDB: {e}")

        # 2. Automatically index shared local knowledge and docs on startup.
        # User uploads are indexed explicitly by the authenticated upload
        # controller; treating data/uploads as SYSTEM_SCOPE would expose a
        # private upload to every user and also duplicate the fresh index.
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        local_dirs = [
            os.path.join(base_dir, "data", "knowledge"),
            os.path.join(base_dir, "data", "docs")
        ]

        files_indexed = 0
        for local_dir in local_dirs:
            if os.path.exists(local_dir):
                    files_indexed += self.index_directory(local_dir, user_id=SYSTEM_SCOPE)
            
        if files_indexed > 0 or len(self.documents) > 0:
            ajax_logger.info(f"RAG Knowledge Store initialized: {len(self.documents)} total chunks ready for instant retrieval.")

    def index_directory(self, dir_path: str, user_id: str = SYSTEM_SCOPE) -> int:
        if not os.path.exists(dir_path):
            return 0
        count = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                if self.index_file(file_path, user_id=user_id):
                    count += 1
        return count

    def index_file(self, file_path: str, user_id: str = SYSTEM_SCOPE) -> bool:
        self._ensure_initialized()
        source = os.path.abspath(os.path.normpath(file_path))
        content = doc_loader.load_file(source)
        if not content:
            return False

        # Re-indexing is idempotent: replace old chunks for this source first.
        self._remove_source_from_memory(source, user_id=user_id)
        self._remove_source_from_mongo(source, user_id=user_id)

        chunks = doc_loader.chunk_text(content)
        title = os.path.splitext(os.path.basename(source))[0].replace("wiki_", "").replace("_", " ").title()
        total_chunks = len(chunks)
        mongo_records = []
        for chunk_index, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(
                f"{source}:{chunk_index}:{chunk}".encode("utf-8")
            ).hexdigest()[:20]
            document = {
                "id": chunk_id,
                "user_id": user_id,
                "source": source,
                "file_name": os.path.basename(source),
                "title": title,
                "chunk": chunk,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "tokens": set(tokenize(chunk)),
                "embedding": self.embedding_provider.embed(chunk)
            }
            self.documents.append(document)
            mongo_records.append({k: v for k, v in document.items() if k != "tokens"})

        # Save to MongoDB Atlas if active
        if is_mongo_active() and mongo_records:
            try:
                db = get_mongo_db()
                db.rag_documents.insert_many(mongo_records)
            except Exception as e:
                ajax_logger.warning(f"Failed saving RAG chunks to MongoDB: {e}")

        return True

    def remove_source(self, source: str, user_id: str = SYSTEM_SCOPE) -> int:
        """Remove all indexed chunks belonging to one document source."""
        self._ensure_initialized()
        source_path = os.path.abspath(os.path.normpath(source))
        removed = self._remove_source_from_memory(source_path, user_id=user_id)
        self._remove_source_from_mongo(source_path, user_id=user_id)
        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Return lightweight retrieval/index statistics for diagnostics."""
        self._ensure_initialized()
        sources = {self._source_key(doc.get("source")) for doc in self.documents}
        return {
            "chunks": len(self.documents),
            "sources": len(sources),
            "source_names": sorted({doc.get("file_name", "") for doc in self.documents if doc.get("file_name")})
        }

    def query(self, search_text: str, top_k: int = 3, user_id: str = SYSTEM_SCOPE) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        # Exclude common query stop words for cleaner matching
        stopwords = {"tell", "me", "about", "what", "is", "who", "was", "explain", "the", "a", "an", "of", "in", "and", "kya", "hai", "batao", "ke", "bare", "mein", "aur", "ko"}
        raw_tokens = tokenize(search_text)
        query_tokens = [t for t in raw_tokens if t not in stopwords] or raw_tokens
        
        if not query_tokens or not self.documents:
            return []

        # Document frequency for IDF
        visible_documents = [
            document for document in self.documents
            if document.get("user_id", SYSTEM_SCOPE) in {SYSTEM_SCOPE, user_id}
        ]
        total_docs = len(visible_documents)
        doc_freq: Dict[str, int] = {}
        for t in set(query_tokens):
            doc_freq[t] = sum(1 for d in visible_documents if t in d["tokens"])

        query_lower = search_text.lower().strip()
        scored_docs: List[Tuple[float, Dict[str, Any]]] = []
        query_embedding = self.embedding_provider.embed(search_text)
        for doc in visible_documents:
            score = 0.0
            doc_tokens = doc["tokens"]
            title_tokens = set(tokenize(doc.get("title", "")))

            for t in query_tokens:
                if t in doc_tokens:
                    df = doc_freq.get(t, 1)
                    idf = math.log((total_docs + 1) / (df + 0.5)) + 1.0
                    score += idf
                if t in title_tokens:
                    score += 2.0  # Significant boost for exact title/topic match

            if len(query_tokens) > 1 and query_lower in doc.get("chunk", "").lower():
                score += 3.0

            semantic_score = self.embedding_provider.cosine(query_embedding, doc.get("embedding") or [])
            score += max(0.0, semantic_score) * 4.0

            if score > 0:
                # Normalize by chunk length
                length_norm = math.sqrt(len(doc_tokens) or 1)
                final_score = score / length_norm
                scored_docs.append((final_score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = []
        for rank, (score, doc) in enumerate(scored_docs[:top_k], 1):
            result = {k: v for k, v in doc.items() if k not in {"tokens", "embedding"}}
            source_name = result.get("file_name") or os.path.basename(result.get("source", ""))
            chunk_index = int(result.get("chunk_index", 0)) + 1
            total_chunks = int(result.get("total_chunks", 1))
            result["score"] = round(score, 4)
            result["rank"] = rank
            result["citation"] = f"{result.get('title', 'Document')} - {source_name}, chunk {chunk_index}/{total_chunks}"
            results.append(result)
        return results


rag_store = RAGStore()
