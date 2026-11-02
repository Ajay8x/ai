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
from database.db import is_mongo_active, get_mongo_db
from core.logger import ajax_logger

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

class RAGStore:
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self._initialized = False

    @staticmethod
    def _source_key(source: Any) -> str:
        source_text = str(source or "")
        if not source_text or source_text == "mongodb_cloud":
            return source_text
        return os.path.normcase(os.path.abspath(source_text))

    def _remove_source_from_memory(self, source: str) -> int:
        source_key = self._source_key(source)
        before = len(self.documents)
        self.documents = [
            doc for doc in self.documents
            if self._source_key(doc.get("source")) != source_key
        ]
        return before - len(self.documents)

    def _remove_source_from_mongo(self, source: str):
        if not is_mongo_active():
            return
        try:
            get_mongo_db().rag_documents.delete_many({"source": source})
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
                        "tokens": set(tokenize(chunk))
                    })
                if mongo_docs:
                    ajax_logger.info(f"Loaded {len(mongo_docs)} RAG document chunks from MongoDB Atlas.")
            except Exception as e:
                ajax_logger.warning(f"Failed loading RAG docs from MongoDB: {e}")

        # 2. Automatically index local knowledge, docs, and persistent uploads on startup
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        local_dirs = [
            os.path.join(base_dir, "data", "knowledge"),
            os.path.join(base_dir, "data", "docs"),
            os.path.join(base_dir, "data", "uploads")
        ]

        files_indexed = 0
        for local_dir in local_dirs:
            if os.path.exists(local_dir):
                files_indexed += self.index_directory(local_dir)
            
        if files_indexed > 0 or len(self.documents) > 0:
            ajax_logger.info(f"RAG Knowledge Store initialized: {len(self.documents)} total chunks ready for instant retrieval.")

    def index_directory(self, dir_path: str) -> int:
        if not os.path.exists(dir_path):
            return 0
        count = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                if self.index_file(file_path):
                    count += 1
        return count

    def index_file(self, file_path: str) -> bool:
        self._ensure_initialized()
        source = os.path.abspath(os.path.normpath(file_path))
        content = doc_loader.load_file(source)
        if not content:
            return False

        # Re-indexing is idempotent: replace old chunks for this source first.
        self._remove_source_from_memory(source)
        self._remove_source_from_mongo(source)

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
                "source": source,
                "file_name": os.path.basename(source),
                "title": title,
                "chunk": chunk,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "tokens": set(tokenize(chunk))
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

    def remove_source(self, source: str) -> int:
        """Remove all indexed chunks belonging to one document source."""
        self._ensure_initialized()
        source_path = os.path.abspath(os.path.normpath(source))
        removed = self._remove_source_from_memory(source_path)
        self._remove_source_from_mongo(source_path)
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

    def query(self, search_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        # Exclude common query stop words for cleaner matching
        stopwords = {"tell", "me", "about", "what", "is", "who", "was", "explain", "the", "a", "an", "of", "in", "and", "kya", "hai", "batao", "ke", "bare", "mein", "aur", "ko"}
        raw_tokens = tokenize(search_text)
        query_tokens = [t for t in raw_tokens if t not in stopwords] or raw_tokens
        
        if not query_tokens or not self.documents:
            return []

        # Document frequency for IDF
        total_docs = len(self.documents)
        doc_freq: Dict[str, int] = {}
        for t in set(query_tokens):
            doc_freq[t] = sum(1 for d in self.documents if t in d["tokens"])

        query_lower = search_text.lower().strip()
        scored_docs: List[Tuple[float, Dict[str, Any]]] = []
        for doc in self.documents:
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

            if score > 0:
                # Normalize by chunk length
                length_norm = math.sqrt(len(doc_tokens) or 1)
                final_score = score / length_norm
                scored_docs.append((final_score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = []
        for rank, (score, doc) in enumerate(scored_docs[:top_k], 1):
            result = {k: v for k, v in doc.items() if k != "tokens"}
            source_name = result.get("file_name") or os.path.basename(result.get("source", ""))
            chunk_index = int(result.get("chunk_index", 0)) + 1
            total_chunks = int(result.get("total_chunks", 1))
            result["score"] = round(score, 4)
            result["rank"] = rank
            result["citation"] = f"{result.get('title', 'Document')} - {source_name}, chunk {chunk_index}/{total_chunks}"
            results.append(result)
        return results


rag_store = RAGStore()
