"""
AJAX AI - Knowledge Vector Store & RAG Pipeline
Fast local document indexing and semantic retrieval.
"""

import os
import re
import math
from typing import List, Dict, Any, Tuple
from ai.rag.loader import doc_loader
from database.db import is_mongo_active, get_mongo_db
from core.logger import ajax_logger

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

class RAGStore:
    def __init__(self):
        self.documents: List[Dict[str, Any]] = [] # [{ "source": path, "chunk": text, "tokens": [...] }]
        
        # 1. Load documents from MongoDB Atlas if active
        if is_mongo_active():
            try:
                db = get_mongo_db()
                mongo_docs = list(db.rag_documents.find({}, {"_id": 0}))
                for doc in mongo_docs:
                    chunk = doc.get("chunk", "")
                    self.documents.append({
                        "source": doc.get("source", "mongodb_cloud"),
                        "title": doc.get("title", "Cloud Document"),
                        "chunk": chunk,
                        "tokens": set(tokenize(chunk))
                    })
                if mongo_docs:
                    ajax_logger.info(f"Loaded {len(mongo_docs)} RAG document chunks from MongoDB Atlas.")
            except Exception as e:
                ajax_logger.warning(f"Failed loading RAG docs from MongoDB: {e}")

        # 2. Automatically index local knowledge directories on startup
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        knowledge_dir = os.path.join(base_dir, "data", "knowledge")
        docs_dir = os.path.join(base_dir, "data", "docs")

        files_indexed = 0
        if os.path.exists(knowledge_dir):
            files_indexed += self.index_directory(knowledge_dir)
        if os.path.exists(docs_dir):
            files_indexed += self.index_directory(docs_dir)
            
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
        content = doc_loader.load_file(file_path)
        if not content:
            return False
        chunks = doc_loader.chunk_text(content)
        title = os.path.splitext(os.path.basename(file_path))[0].replace("wiki_", "").replace("_", " ").title()
        mongo_records = []
        for chunk in chunks:
            self.documents.append({
                "source": file_path,
                "title": title,
                "chunk": chunk,
                "tokens": set(tokenize(chunk))
            })
            mongo_records.append({
                "source": file_path,
                "title": title,
                "chunk": chunk
            })

        # Save to MongoDB Atlas if active
        if is_mongo_active() and mongo_records:
            try:
                db = get_mongo_db()
                db.rag_documents.insert_many(mongo_records)
            except Exception as e:
                ajax_logger.warning(f"Failed saving RAG chunks to MongoDB: {e}")

        return True

    def query(self, search_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
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

            if score > 0:
                # Normalize by chunk length
                length_norm = math.sqrt(len(doc_tokens) or 1)
                final_score = score / length_norm
                scored_docs.append((final_score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_docs[:top_k]]


rag_store = RAGStore()
