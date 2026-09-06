from typing import Any, Dict, List, Set
import networkx as nx
from app.graph.knowledge_graph import KnowledgeGraph


class GraphTraverser:
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.graph = kg.graph

    def find_matching_nodes(self, query_terms: List[str]) -> List[str]:
        matched_nodes: Set[str] = set()
        normalized_terms = [t.strip().lower() for t in query_terms if t.strip()]

        for node_id, data in self.graph.nodes(data=True):
            canonical = data.get("canonical_name", "").lower()
            aliases = [a.lower() for a in data.get("aliases", [])]

            for term in normalized_terms:
                if term in node_id or term in canonical or any(term in a for a in aliases):
                    matched_nodes.add(node_id)

        return list(matched_nodes)

    def extract_subgraph_khop(
        self,
        seed_nodes: List[str],
        k_hops: int = 1,
        max_nodes: int = 50
    ) -> Dict[str, Any]:
        valid_seeds = [node.strip().lower() for node in seed_nodes if self.graph.has_node(node.strip().lower())]
        if not valid_seeds:
            return {"nodes": [], "edges": []}

        # Convert directed multi-graph to undirected for symmetric neighborhood reachability
        undirected_view = self.graph.to_undirected(as_view=True)
        nodes_to_include: Set[str] = set()

        for seed in valid_seeds:
            lengths = nx.single_source_shortest_path_length(undirected_view, seed, cutoff=k_hops)
            nodes_to_include.update(lengths.keys())

        # Cap sub-graph size if traversal grows beyond limit
        if len(nodes_to_include) > max_nodes:
            # Retain seed nodes first, slice remainder
            remainder = list(nodes_to_include - set(valid_seeds))[: (max_nodes - len(valid_seeds))]
            nodes_to_include = set(valid_seeds) | set(remainder)

        sub = self.graph.subgraph(nodes_to_include)

        nodes = []
        for n, data in sub.nodes(data=True):
            nodes.append({"id": n, **data})

        edges = []
        for u, v, k, data in sub.edges(data=True, keys=True):
            edges.append({"source": u, "target": v, "key": k, **data})

        return {"nodes": nodes, "edges": edges}

    def find_paths_between(
        self,
        source_name: str,
        target_name: str,
        max_depth: int = 3
    ) -> List[List[str]]:
        src = source_name.strip().lower()
        tgt = target_name.strip().lower()

        if not self.graph.has_node(src) or not self.graph.has_node(tgt):
            return []

        # Find simple paths within directed graph
        paths = list(nx.all_simple_paths(self.graph, source=src, target=tgt, cutoff=max_depth))
        return paths