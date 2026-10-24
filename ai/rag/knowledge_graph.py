"""
AJAX AI - Multi-Relational Knowledge Graph Store
Stores entities as nodes and relationships as edges using NetworkX.
Provides fast multi-hop traversal, subgraph extraction, and persistence.
"""

import os
import json
from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx
from core.logger import ajax_logger


class KnowledgeGraphStore:
    """
    In-memory and disk-persisted Knowledge Graph powered by NetworkX.
    """
    def __init__(self, storage_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_path = storage_path or os.path.join(base_dir, "data", "knowledge", "graph_db.json")
        self.graph = nx.MultiDiGraph()
        self.load()

    def add_node(self, name: str, node_type: str = "CONCEPT", **attributes) -> str:
        clean_name = (name or "").strip()
        if not clean_name:
            return ""
        
        node_id = clean_name.lower()
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, name=clean_name, type=node_type, frequency=1, **attributes)
        else:
            self.graph.nodes[node_id]["frequency"] = self.graph.nodes[node_id].get("frequency", 1) + 1
            for k, v in attributes.items():
                self.graph.nodes[node_id][k] = v
        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        doc_id: str = "",
        evidence: str = "",
        weight: float = 1.0
    ):
        src_id = self.add_node(source)
        tgt_id = self.add_node(target)
        if not src_id or not tgt_id or src_id == tgt_id:
            return

        clean_rel = (relation or "RELATES_TO").strip().upper().replace(" ", "_")

        # Check if identical edge already exists
        if self.graph.has_edge(src_id, tgt_id):
            for edge_key, data in self.graph.get_edge_data(src_id, tgt_id).items():
                if data.get("relation") == clean_rel:
                    data["weight"] = data.get("weight", 1.0) + 1.0
                    if doc_id and doc_id not in data.get("docs", []):
                        data.setdefault("docs", []).append(doc_id)
                    return

        self.graph.add_edge(
            src_id,
            tgt_id,
            relation=clean_rel,
            doc_id=doc_id,
            evidence=evidence,
            weight=weight,
            docs=[doc_id] if doc_id else []
        )

    def find_node_id(self, entity_name: str) -> Optional[str]:
        """Finds node id by exact or case-insensitive name match."""
        name_lower = entity_name.strip().lower()
        if self.graph.has_node(name_lower):
            return name_lower
        
        for n, data in self.graph.nodes(data=True):
            if data.get("name", "").lower() == name_lower:
                return n
        return None

    def extract_subgraph(
        self,
        seed_entities: List[str],
        max_hops: int = 2,
        max_nodes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Extracts 1-hop or 2-hop connected subgraph around seed entities.
        Returns a list of structured edge dictionaries:
        [{ source: "...", relation: "...", target: "...", doc_id: "..." }]
        """
        if not seed_entities or len(self.graph) == 0:
            return []

        # 1. Match seed entities to graph node IDs
        seed_node_ids: Set[str] = set()
        for seed in seed_entities:
            matched = self.find_node_id(seed)
            if matched:
                seed_node_ids.add(matched)
            else:
                # Substring matching for fuzzy match
                seed_l = seed.lower()
                for n, data in self.graph.nodes(data=True):
                    if seed_l in n or n in seed_l:
                        seed_node_ids.add(n)

        if not seed_node_ids:
            return []

        # 2. Multi-hop Breadth-First Search (BFS) Expansion
        collected_nodes: Set[str] = set(seed_node_ids)
        current_frontier = set(seed_node_ids)

        for _ in range(max_hops):
            next_frontier = set()
            for node in current_frontier:
                if len(collected_nodes) >= max_nodes:
                    break
                # Both successors and predecessors (undirected exploration)
                neighbors = set(self.graph.successors(node)) | set(self.graph.predecessors(node))
                for neighbor in neighbors:
                    if neighbor not in collected_nodes:
                        next_frontier.add(neighbor)
                        collected_nodes.add(neighbor)
                        if len(collected_nodes) >= max_nodes:
                            break
            current_frontier = next_frontier
            if not current_frontier or len(collected_nodes) >= max_nodes:
                break

        # 3. Collect all edges between the gathered nodes
        subgraph_edges: List[Dict[str, Any]] = []
        for u in collected_nodes:
            for v in self.graph.successors(u):
                if v in collected_nodes:
                    edge_dict = self.graph.get_edge_data(u, v)
                    u_name = self.graph.nodes[u].get("name", u)
                    v_name = self.graph.nodes[v].get("name", v)
                    for _, data in edge_dict.items():
                        subgraph_edges.append({
                            "source": u_name,
                            "relation": data.get("relation", "RELATES_TO"),
                            "target": v_name,
                            "doc_id": data.get("doc_id", ""),
                            "weight": data.get("weight", 1.0)
                        })

        # Sort edges by weight/importance
        subgraph_edges.sort(key=lambda x: x.get("weight", 1.0), reverse=True)
        return subgraph_edges

    def find_multi_hop_path(self, start_entity: str, end_entity: str) -> Optional[List[Dict[str, str]]]:
        """
        Finds the shortest semantic reasoning path connecting two entities.
        """
        src_id = self.find_node_id(start_entity)
        tgt_id = self.find_node_id(end_entity)
        if not src_id or not tgt_id:
            return None

        try:
            # Undirected shortest path
            undirected = self.graph.to_undirected()
            path_nodes = nx.shortest_path(undirected, source=src_id, target=tgt_id)
            
            steps = []
            for i in range(len(path_nodes) - 1):
                u = path_nodes[i]
                v = path_nodes[i+1]
                u_name = self.graph.nodes[u].get("name", u)
                v_name = self.graph.nodes[v].get("name", v)
                
                # Fetch relation
                rel = "CONNECTED_TO"
                if self.graph.has_edge(u, v):
                    data = list(self.graph.get_edge_data(u, v).values())[0]
                    rel = data.get("relation", rel)
                elif self.graph.has_edge(v, u):
                    data = list(self.graph.get_edge_data(v, u).values())[0]
                    rel = f"INVERSE_{data.get('relation', rel)}"
                
                steps.append({"from": u_name, "relation": rel, "to": v_name})
            return steps
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def linearize_subgraph(self, edges: List[Dict[str, Any]]) -> str:
        """
        Formats extracted subgraph edges into clean triples representation for LLM context.
        """
        if not edges:
            return "No connected graph relationships found."

        triples = []
        for e in edges:
            src = e["source"]
            rel = e["relation"]
            tgt = e["target"]
            triples.append(f"• ({src}) ──[{rel}]──> ({tgt})")
        return "\n".join(triples)

    def save(self):
        """Persists graph structure to JSON."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "nodes": [
                    {"id": n, **attrs} for n, attrs in self.graph.nodes(data=True)
                ],
                "edges": [
                    {
                        "source": u,
                        "target": v,
                        **data
                    }
                    for u, v, data in self.graph.edges(data=True)
                ]
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            ajax_logger.warning(f"Could not save Knowledge Graph to {self.storage_path}: {e}")

    def load(self):
        """Loads graph structure from JSON file if it exists."""
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.graph.clear()
            for node in data.get("nodes", []):
                nid = node.pop("id")
                self.graph.add_node(nid, **node)

            for edge in data.get("edges", []):
                src = edge.pop("source")
                tgt = edge.pop("target")
                self.graph.add_edge(src, tgt, **edge)

            ajax_logger.info(f"Loaded Knowledge Graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")
        except Exception as e:
            ajax_logger.warning(f"Failed loading Knowledge Graph ({e}). Starting fresh.")

    def get_stats(self) -> Dict[str, Any]:
        """Returns topological statistics of the knowledge graph."""
        nodes_count = self.graph.number_of_nodes()
        edges_count = self.graph.number_of_edges()
        
        # Calculate top central nodes if graph has nodes
        top_entities = []
        if nodes_count > 0:
            degrees = dict(self.graph.degree())
            sorted_deg = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
            for nid, deg in sorted_deg:
                name = self.graph.nodes[nid].get("name", nid)
                top_entities.append({"name": name, "connections": deg})

        return {
            "total_entities": nodes_count,
            "total_relationships": edges_count,
            "top_connected_entities": top_entities
        }


# Singleton instance
knowledge_graph = KnowledgeGraphStore()
