"""
AJAX AI - Search-Guided Hybrid GraphRAG Pipeline
Combines Meilisearch fast text retrieval with Knowledge Graph subgraph extraction
to feed multi-hop grounded context into LLMs, drastically reducing hallucinations.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from ai.rag.loader import doc_loader
from ai.rag.meili_store import meili_store
from ai.rag.entity_extractor import entity_extractor
from ai.rag.knowledge_graph import knowledge_graph
from core.logger import ajax_logger


class GraphRAGPipeline:
    """
    Search-Guided GraphRAG Orchestrator.
    Step 1: Ingest documents -> Extract Entities & Relations -> Store in Meilisearch & Knowledge Graph.
    Step 2: Query -> Meilisearch fast lookup -> Extract Seed Entities -> Traverse Subgraph -> Prompt LLM.
    """
    def __init__(self):
        self.meili = meili_store
        self.graph = knowledge_graph
        self.extractor = entity_extractor

    def index_text(
        self,
        text: str,
        title: str = "Document",
        source: str = "manual_entry",
        use_llm_extractor: bool = False
    ) -> Dict[str, Any]:
        """
        Ingests raw text into both Meilisearch index and Knowledge Graph.
        """
        if not text or not text.strip():
            return {"success": False, "chunks": 0, "entities": 0, "relations": 0}

        chunks = doc_loader.chunk_text(text, chunk_size=500, overlap=50)
        indexed_docs = []
        total_entities = 0
        total_relations = 0

        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{source}_{i}_{chunk[:30]}".encode()).hexdigest()[:16]

            # Extract entities and relations
            if use_llm_extractor:
                entities, relations = self.extractor.extract_with_llm(chunk)
            else:
                entities, relations = self.extractor.extract_heuristic(chunk)

            entity_names = [e["name"] for e in entities]
            total_entities += len(entities)
            total_relations += len(relations)

            # 1. Update Knowledge Graph
            for ent in entities:
                self.graph.add_node(ent["name"], node_type=ent.get("type", "CONCEPT"), doc_id=chunk_id)

            for rel in relations:
                self.graph.add_edge(
                    source=rel["source"],
                    target=rel["target"],
                    relation=rel["relation"],
                    doc_id=chunk_id,
                    evidence=chunk[:200]
                )

            # 2. Prepare Meilisearch Document
            indexed_docs.append({
                "id": chunk_id,
                "title": title,
                "content": chunk,
                "source": source,
                "entities": entity_names,
                "chunk_index": i
            })

        # Save to Meilisearch
        self.meili.add_documents(indexed_docs)
        # Save Knowledge Graph to disk
        self.graph.save()

        ajax_logger.info(
            f"GraphRAG indexed '{title}': {len(chunks)} chunks, {total_entities} entities, {total_relations} relations."
        )

        return {
            "success": True,
            "chunks": len(chunks),
            "entities": total_entities,
            "relations": total_relations,
            "title": title
        }

    def index_file(self, file_path: str, use_llm_extractor: bool = False) -> Dict[str, Any]:
        """
        Loads and indexes any supported file (PDF, TXT, MD, DOCX, Code) into GraphRAG.
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        content = doc_loader.load_file(file_path)
        if not content:
            return {"success": False, "error": f"Could not read content from {file_path}"}

        title = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ").title()
        return self.index_text(
            text=content,
            title=title,
            source=file_path,
            use_llm_extractor=use_llm_extractor
        )

    def retrieve(self, query: str, top_k: int = 3, max_hops: int = 2) -> Dict[str, Any]:
        """
        Core Search-Guided Subgraph Retrieval:
        1. Fast text search via Meilisearch to find top chunks.
        2. Identify seed entities from query + top chunks.
        3. Traverse Knowledge Graph around seeds to extract multi-hop subgraph.
        """
        # Step 1: Fast text search
        matched_chunks = self.meili.search(query, top_k=top_k)

        # Step 2: Extract seed entities
        seeds = set(self.extractor.extract_from_query(query))
        for hit in matched_chunks:
            for ent in hit.get("entities", []):
                seeds.add(ent)

        # Step 3: Graph Traversal
        subgraph_edges = self.graph.extract_subgraph(
            seed_entities=list(seeds),
            max_hops=max_hops,
            max_nodes=25
        )

        # Step 4: Linearize subgraph into readable triples
        triples_text = self.graph.linearize_subgraph(subgraph_edges)

        # Step 5: Format context block
        chunks_formatted = []
        for i, hit in enumerate(matched_chunks, 1):
            src = hit.get("source", "Unknown")
            cnt = hit.get("content", "")
            chunks_formatted.append(f"[{i}] Source: {src}\n{cnt}")

        full_context = (
            "=== [VERIFIED KNOWLEDGE GRAPH RELATIONSHIPS (GROUND TRUTH)] ===\n"
            f"{triples_text}\n\n"
            "=== [SUPPORTING SOURCE PASSAGES] ===\n"
            + ("\n\n---\n\n".join(chunks_formatted) if chunks_formatted else "No direct text matches found.")
        )

        return {
            "query": query,
            "seeds": list(seeds),
            "matched_chunks": matched_chunks,
            "subgraph_edges": subgraph_edges,
            "triples_text": triples_text,
            "formatted_context": full_context
        }

    def answer(self, query: str, top_k: int = 3, max_hops: int = 2) -> Dict[str, Any]:
        """
        End-to-End Grounded Answer Generation:
        Retrieves hybrid subgraph context and prompts the LLM to generate a verified response.
        """
        retrieval = self.retrieve(query, top_k=top_k, max_hops=max_hops)

        # If completely empty
        if not retrieval["matched_chunks"] and not retrieval["subgraph_edges"]:
            return {
                "answer": "No relevant entities or documents found in the Knowledge Graph for this query.",
                "retrieval": retrieval
            }

        system_instruction = (
            "You are AJAX AI's Grounded Knowledge Assistant powered by GraphRAG.\n"
            "Your task is to answer the user query STRICTLY based on the provided Knowledge Graph Relationships and Source Passages.\n"
            "CRITICAL RULES:\n"
            "1. Ground your answer in the relationship triples. Use them to connect multi-hop concepts.\n"
            "2. Never hallucinate facts or connections not present in the context.\n"
            "3. If the graph explicitly connects entities, explain that connection clearly.\n"
            "4. Provide a clear, natural response in the same language as the user query."
        )

        user_content = (
            f"Context Information:\n{retrieval['formatted_context']}\n\n"
            f"User Question: {query}\n\n"
            "Please provide a well-structured, grounded answer:"
        )

        try:
            from ai.llm.factory import llm_brain
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ]
            response = llm_brain.generate(messages, temperature=0.2, max_tokens=1024)
            answer_text = response.content or "Could not generate answer."
        except Exception as e:
            answer_text = f"Context retrieved successfully, but LLM generation encountered an error: {e}"

        return {
            "answer": answer_text,
            "seeds_used": retrieval["seeds"],
            "subgraph_triples": retrieval["subgraph_edges"],
            "matched_sources": [c.get("source") for c in retrieval["matched_chunks"]],
            "retrieval": retrieval
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Returns overall health and statistics of GraphRAG."""
        return {
            "meilisearch": self.meili.get_stats(),
            "knowledge_graph": self.graph.get_stats()
        }


# Singleton instance
graph_rag = GraphRAGPipeline()
