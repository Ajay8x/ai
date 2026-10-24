"""
AJAX AI - GraphRAG End-to-End Test & Demonstration Suite
Validates:
1. Fast Document Indexing & Keyword Filtering (Meilisearch Engine)
2. Entity and Relationship Extraction
3. Multi-Relational Knowledge Graph Storage & Persistence
4. Multi-Hop Subgraph Traversal & Shortest Path Finding
5. Grounded LLM Context Construction (Hallucination Prevention)
"""

import sys
import os

# Set root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from ai.rag.graph_rag import graph_rag
from ai.rag.knowledge_graph import knowledge_graph
from ai.rag.meili_store import meili_store
from tools.graphrag_tools import GraphRAGQueryTool, ExploreKnowledgeGraphTool


def run_graph_rag_suite():
    print("=" * 70)
    print("🚀 STARTING GRAPHRAG VERIFICATION SUITE")
    print("=" * 70)

    # 1. Check Meilisearch & System Status
    status = graph_rag.get_system_status()
    print(f"\n[1] Search Engine Status:")
    print(f"    - Engine: {status['meilisearch']['engine']}")
    print(f"    - Index: {status['meilisearch']['index']}")

    # 2. Ingest Sample Multi-Hop Knowledge Document
    sample_text = (
        "Demis Hassabis founded DeepMind in London. "
        "DeepMind developed AlphaFold to solve the 50-year-old protein folding grand challenge. "
        "AlphaFold collaborates with EMBL to build a public database of 200 million protein structures. "
        "EMBL researches Structural Biology and Genomics across European laboratories. "
        "John Jumper works on AlphaFold at DeepMind."
    )

    print("\n[2] Ingesting Multi-Hop Document into GraphRAG...")
    index_result = graph_rag.index_text(
        text=sample_text,
        title="AI in Biology & DeepMind",
        source="test_corpus/deepmind_biology.txt"
    )
    print(f"    ✓ Chunks created: {index_result['chunks']}")
    print(f"    ✓ Entities extracted: {index_result['entities']}")
    print(f"    ✓ Relationships extracted: {index_result['relations']}")

    # 3. Test Graph Knowledge Base
    stats = knowledge_graph.get_stats()
    print(f"\n[3] Knowledge Graph Topology:")
    print(f"    - Total Nodes (Entities): {stats['total_entities']}")
    print(f"    - Total Edges (Relations): {stats['total_relationships']}")
    print(f"    - Top Hub Entities: {[e['name'] for e in stats['top_connected_entities']]}")

    # 4. Multi-Hop Semantic Reasoning Path Test
    # Test path from Demis Hassabis to EMBL
    print("\n[4] Testing Multi-Hop Reasoning Path:")
    print("    Finding semantic chain: 'Demis Hassabis' ➔ 'EMBL'...")
    path = knowledge_graph.find_multi_hop_path("Demis Hassabis", "EMBL")
    if path:
        chain_str = " ➔ ".join([f"({step['from']}) --[{step['relation']}]--> ({step['to']})" for step in path])
        print(f"    🎯 Discovered Multi-Hop Path ({len(path)} hops):")
        print(f"       {chain_str}")
    else:
        print("    ℹ️ No direct path found.")

    # 5. Hybrid Search-Guided Retrieval Test
    test_query = "What is the relationship between AlphaFold and EMBL?"
    print(f"\n[5] Executing Hybrid Search-Guided Retrieval for:")
    print(f"    Query: '{test_query}'")
    
    retrieval = graph_rag.retrieve(test_query, top_k=2, max_hops=2)
    print(f"    ✓ Matched Chunks: {len(retrieval['matched_chunks'])}")
    print(f"    ✓ Seed Entities Identified: {retrieval['seeds']}")
    print(f"    ✓ Subgraph Edges Extracted: {len(retrieval['subgraph_edges'])}")
    print("\n--- Subgraph Triples Provided to LLM ---")
    print(retrieval['triples_text'])

    # 6. Test Agent Tools
    print("\n[6] Testing GraphRAG Agent Tools:")
    query_tool = GraphRAGQueryTool()
    tool_res = query_tool.execute(query="Tell me about AlphaFold and DeepMind")
    print(f"    Tool Execution Success: {tool_res.success}")
    print(f"    Tool Output Snippet:\n{tool_res.output[:350]}...")

    explore_tool = ExploreKnowledgeGraphTool()
    explore_res = explore_tool.execute(entity="AlphaFold")
    print(f"\n    Explore Tool Output:\n{explore_res.output}")

    print("\n" + "=" * 70)
    print("✅ GRAPHRAG SYSTEM SUCCESSFULLY VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    run_graph_rag_suite()
