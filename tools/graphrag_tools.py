"""
AJAX AI - GraphRAG Execution Tools
Exposes Search-Guided Hybrid GraphRAG queries and knowledge graph exploration to the AI Agent.
"""

from typing import Dict, Any, Optional
from tools.base import BaseTool, ToolResult
from core.permissions import PermissionLevel, ToolCategory
from ai.rag.graph_rag import graph_rag
from ai.rag.knowledge_graph import knowledge_graph


class GraphRAGQueryTool(BaseTool):
    name = "graphrag_query"
    description = (
        "Search knowledge base using GraphRAG (Meilisearch + Knowledge Graph). "
        "Extracts connected subgraphs and relationship triples to answer multi-hop or complex queries with zero hallucination."
    )
    category = ToolCategory.FILESYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Question or topic to query via GraphRAG"
            },
            "max_hops": {
                "type": "integer",
                "description": "Maximum graph traversal hops (default: 2)",
                "default": 2
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, max_hops: int = 2, **kwargs) -> ToolResult:
        result = graph_rag.answer(query, top_k=3, max_hops=max_hops)
        answer = result.get("answer", "")
        triples = result.get("subgraph_triples", [])
        
        triples_summary = ""
        if triples:
            triples_summary = "\n\nKnowledge Graph Triples Consulted:\n" + "\n".join(
                [f"- ({t['source']}) --[{t['relation']}]--> ({t['target']})" for t in triples[:10]]
            )

        output = f"{answer}{triples_summary}"
        return ToolResult(success=True, output=output, metadata=result)


class IndexToGraphRAGTool(BaseTool):
    name = "index_to_graphrag"
    description = "Indexes a document, file path, or raw text into Meilisearch and the Knowledge Graph."
    category = ToolCategory.FILESYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "content_or_path": {
                "type": "string",
                "description": "File path (e.g., 'data/docs/sample.pdf') or raw text to index"
            },
            "title": {
                "type": "string",
                "description": "Optional title for the document",
                "default": "Custom Document"
            }
        },
        "required": ["content_or_path"]
    }

    def execute(self, content_or_path: str, title: str = "Custom Document", **kwargs) -> ToolResult:
        import os
        if os.path.exists(content_or_path):
            res = graph_rag.index_file(content_or_path)
        else:
            res = graph_rag.index_text(content_or_path, title=title)

        if res.get("success"):
            out = f"Successfully indexed '{res.get('title', title)}' into GraphRAG! Chunks: {res.get('chunks', 0)}, Entities: {res.get('entities', 0)}, Relations: {res.get('relations', 0)}."
            return ToolResult(success=True, output=out, metadata=res)
        return ToolResult(success=False, output=res.get("error", "Indexing failed"), error=res.get("error"))


class ExploreKnowledgeGraphTool(BaseTool):
    name = "explore_knowledge_graph"
    description = "Inspect entities, view connected relationships, or find shortest reasoning paths between two entities."
    category = ToolCategory.FILESYSTEM
    permission = PermissionLevel.SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "description": "Entity name to inspect neighbors and relations for"
            },
            "find_path_to": {
                "type": "string",
                "description": "Optional target entity to find multi-hop reasoning path to"
            }
        },
        "required": ["entity"]
    }

    def execute(self, entity: str, find_path_to: Optional[str] = None, **kwargs) -> ToolResult:
        if find_path_to:
            path = knowledge_graph.find_multi_hop_path(entity, find_path_to)
            if not path:
                return ToolResult(success=True, output=f"No connected path found between '{entity}' and '{find_path_to}'.")
            
            steps = " ➔ ".join([f"({s['from']}) --[{s['relation']}]--> ({s['to']})" for s in path])
            output = f"Multi-Hop Semantic Path ({len(path)} steps):\n{steps}"
            return ToolResult(success=True, output=output, metadata={"path": path})

        # Neighbor inspection
        subgraph = knowledge_graph.extract_subgraph([entity], max_hops=1, max_nodes=15)
        if not subgraph:
            return ToolResult(success=True, output=f"No relationships found for entity '{entity}' in the graph.")

        triples = [f"• ({t['source']}) ──[{t['relation']}]──> ({t['target']})" for t in subgraph]
        output = f"Graph Connections for '{entity}':\n" + "\n".join(triples)
        return ToolResult(success=True, output=output, metadata={"subgraph": subgraph})
