"""
AJAX AI - Knowledge Vector Store & RAG Pipeline
Fast local document indexing and semantic retrieval.
"""

import os
import re
import math
from typing import List, Dict, Any, Tuple
from ai.rag.loader import doc_loader
from core.logger import ajax_logger

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

class RAGStore:
    def __init__(self):
        self.documents: List[Dict[str, Any]] = [] # [{ "source": path, "chunk": text, "tokens": [...] }]
        
        # Automatically index knowledge directories on startup
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        knowledge_dir = os.path.join(base_dir, "data", "knowledge")
        docs_dir = os.path.join(base_dir, "data", "docs")

        files_indexed = 0
        if os.path.exists(knowledge_dir):
            files_indexed += self.index_directory(knowledge_dir)
        if os.path.exists(docs_dir):
            files_indexed += self.index_directory(docs_dir)
            
        if files_indexed > 0:
            ajax_logger.info(f"RAG Knowledge Store initialized: {files_indexed} documents ({len(self.documents)} total chunks) ready for instant retrieval.")

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
        for chunk in chunks:
            self.documents.append({
                "source": file_path,
                "title": os.path.splitext(os.path.basename(file_path))[0].replace("wiki_", "").replace("_", " ").title(),
                "chunk": chunk,
                "tokens": set(tokenize(chunk))
            })
        return True

    def query(self, search_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # Exclude common query stop words for cleaner matching
        stopwords = {"tell", "me", "about", "what", "is", "who", "was", "explain", "the", "a", "an", "of", "in", "and", "kya", "hai", "batao", "ke", "bare", "mein"}
        raw_tokens = tokenize(search_text)
        query_tokens = set([t for t in raw_tokens if t not in stopwords]) or set(raw_tokens)
        
        if not query_tokens or not self.documents:
            return []

        scored_docs: List[Tuple[float, Dict[str, Any]]] = []
        for doc in self.documents:
            intersection = query_tokens & doc["tokens"]
            if intersection:
                score = len(intersection) / (math.sqrt(len(query_tokens)) * math.sqrt(len(doc["tokens"]) or 1))
                # Boost if title matches
                title_tokens = set(tokenize(doc.get("title", "")))
                if query_tokens & title_tokens:
                    score += 0.5
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_docs[:top_k]]

rag_store = RAGStore()
