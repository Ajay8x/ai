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

    def index_directory(self, dir_path: str):
        if not os.path.exists(dir_path):
            return
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                self.index_file(file_path)

    def index_file(self, file_path: str):
        content = doc_loader.load_file(file_path)
        if not content:
            return
        chunks = doc_loader.chunk_text(content)
        for chunk in chunks:
            self.documents.append({
                "source": file_path,
                "chunk": chunk,
                "tokens": set(tokenize(chunk))
            })
        ajax_logger.info(f"Indexed document: {file_path} ({len(chunks)} chunks)")

    def query(self, search_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = set(tokenize(search_text))
        if not query_tokens or not self.documents:
            return []

        scored_docs: List[Tuple[float, Dict[str, Any]]] = []
        for doc in self.documents:
            intersection = query_tokens & doc["tokens"]
            score = len(intersection) / (math.sqrt(len(query_tokens)) * math.sqrt(len(doc["tokens"]) or 1))
            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_docs[:top_k]]

rag_store = RAGStore()
