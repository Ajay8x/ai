"""
AJAX AI - Meilisearch Engine & Ultra-Fast Document Indexer
Provides sub-millisecond lexical keyword filtering, typo-tolerant search,
and automatic fallback to an in-memory inverted index when Meilisearch daemon is offline.
"""

import os
import re
import math
import hashlib
from typing import List, Dict, Any, Optional
from core.logger import ajax_logger

try:
    import meilisearch
    MEILI_LIB_AVAILABLE = True
except ImportError:
    MEILI_LIB_AVAILABLE = False


def _tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', (text or "").lower())


class InvertedIndexFallback:
    """High-speed in-memory BM25-like index used when standalone Meilisearch server is not reachable."""
    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}

    def add_documents(self, docs: List[Dict[str, Any]]):
        for doc in docs:
            doc_id = str(doc.get("id"))
            text = f"{doc.get('title', '')} {doc.get('content', '')} {' '.join(doc.get('entities', []))}"
            tokens = set(_tokenize(text))
            self.documents[doc_id] = {**doc, "_tokens": tokens}

    def search(self, query: str, limit: int = 5, filter_entities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return list(self.documents.values())[:limit]

        scored = []
        for doc_id, doc in self.documents.items():
            doc_tokens = doc["_tokens"]
            score = 0.0
            for qt in query_tokens:
                if qt in doc_tokens:
                    score += 1.0
            
            # Boost if query matches title
            title_tokens = set(_tokenize(doc.get("title", "")))
            for qt in query_tokens:
                if qt in title_tokens:
                    score += 2.0

            # Filter by entities if specified
            if filter_entities:
                doc_ents = set(e.lower() for e in doc.get("entities", []))
                if not any(fe.lower() in doc_ents for fe in filter_entities):
                    continue

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{k: v for k, v in doc.items() if k != "_tokens"} for _, doc in scored[:limit]]

    def delete(self, doc_id: str):
        self.documents.pop(str(doc_id), None)

    def count(self) -> int:
        return len(self.documents)


class MeiliSearchStore:
    """
    Manages indexing and searching documents in Meilisearch.
    Seamlessly falls back to InvertedIndexFallback if Meilisearch instance is offline.
    """
    def __init__(
        self,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: str = "ajax_graphrag"
    ):
        self.host = host or os.getenv("MEILISEARCH_HOST", "http://127.0.0.1:7700")
        self.api_key = api_key or os.getenv("MEILISEARCH_KEY", "")
        self.index_name = os.getenv("MEILISEARCH_INDEX", index_name)
        
        self.client: Optional[Any] = None
        self.index: Optional[Any] = None
        self._is_connected = False
        self.fallback = InvertedIndexFallback()

        self._initialize()

    def _initialize(self):
        if not MEILI_LIB_AVAILABLE:
            ajax_logger.info("meilisearch library not installed, using embedded fast index.")
            return

        try:
            self.client = meilisearch.Client(self.host, self.api_key, timeout=2)
            # Ping health
            health = self.client.health()
            if health.get("status") == "available":
                self.index = self.client.index(self.index_name)
                # Configure searchable and filterable attributes for GraphRAG
                self.index.update_filterable_attributes(["entities", "source", "title", "doc_id"])
                self.index.update_searchable_attributes(["title", "content", "entities"])
                self._is_connected = True
                ajax_logger.info(f"Connected to Meilisearch at {self.host} (index: {self.index_name})")
        except Exception as e:
            self._is_connected = False
            self.client = None
            self.index = None
            ajax_logger.debug(f"Meilisearch offline ({e}). Using ultra-fast embedded inverted index.")

    def is_live_connected(self) -> bool:
        if not self._is_connected or not self.client:
            return False
        try:
            return self.client.health().get("status") == "available"
        except Exception:
            return False

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents / chunks to Meilisearch index.
        Each doc should have: { id, title, content, source, entities, relations }
        """
        if not documents:
            return False

        # Format docs and generate predictable IDs if missing
        clean_docs = []
        for i, doc in enumerate(documents):
            d = dict(doc)
            if "id" not in d or not d["id"]:
                raw_hash = hashlib.md5(f"{d.get('source', '')}_{d.get('content', '')}_{i}".encode()).hexdigest()
                d["id"] = raw_hash[:16]
            # Ensure entities is a list
            if "entities" not in d or not isinstance(d["entities"], list):
                d["entities"] = []
            clean_docs.append(d)

        # Always keep fallback in sync for zero-downtime resilience
        self.fallback.add_documents(clean_docs)

        if self.is_live_connected() and self.index:
            try:
                task = self.index.add_documents(clean_docs, primary_key="id")
                return True
            except Exception as e:
                ajax_logger.warning(f"Failed to add docs to Meilisearch, kept in memory index: {e}")
                return False

        return True

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_entities: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fast lexical search with optional entity filtering.
        """
        if self.is_live_connected() and self.index:
            try:
                search_params: Dict[str, Any] = {"limit": top_k}
                if filter_entities:
                    # Filter condition: entities IN [x, y]
                    escaped_entities = [f'"{e}"' for e in filter_entities]
                    search_params["filter"] = f"entities IN [{', '.join(escaped_entities)}]"
                
                results = self.index.search(query, search_params)
                return results.get("hits", [])
            except Exception as e:
                ajax_logger.warning(f"Meilisearch query failed, falling back: {e}")

        return self.fallback.search(query, limit=top_k, filter_entities=filter_entities)

    def delete_document(self, doc_id: str):
        self.fallback.delete(doc_id)
        if self.is_live_connected() and self.index:
            try:
                self.index.delete_document(doc_id)
            except Exception:
                pass

    def get_stats(self) -> Dict[str, Any]:
        live = self.is_live_connected()
        total_docs = 0
        if live and self.index:
            try:
                stats = self.index.get_stats()
                total_docs = stats.number_of_documents
            except Exception:
                total_docs = self.fallback.count()
        else:
            total_docs = self.fallback.count()

        return {
            "engine": "Meilisearch (Live Server)" if live else "Embedded Fast Inverted Index (Standby)",
            "host": self.host if live else "In-Memory Local",
            "index": self.index_name,
            "total_documents": total_docs,
            "live_connected": live
        }


# Singleton instance
meili_store = MeiliSearchStore()
