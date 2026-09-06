import re
from typing import List, Optional
from app.evidence.schemas import (
    GraphEdgeEvidence,
    GraphNodeEvidence,
    RerankedChunkEvidence,
    SubgraphEvidence,
    UnifiedEvidencePacket,
)
from app.graph.traversal import GraphTraverser
from app.retrieval.pipeline import RetrievalPipeline


class EvidenceAssembler:
    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        graph_traverser: GraphTraverser,
    ):
        self.retrieval_pipeline = retrieval_pipeline
        self.traverser = graph_traverser

    def _extract_query_terms(self, query: str) -> List[str]:
        tokens = re.findall(r"[A-Za-z0-9_\-\.]+", query)
        stopwords = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
            "with", "by", "of", "from", "how", "what", "why", "is", "are",
            "does", "do", "explain", "describe", "between"
        }
        terms = [t for t in tokens if t.lower() not in stopwords and len(t) > 1]
        return terms

    def assemble(
        self,
        query: str,
        text_top_k: int = 5,
        k_hops: int = 1,
        max_subgraph_nodes: int = 30,
    ) -> UnifiedEvidencePacket:
        # Step 1: Text retrieval & cross-encoder reranking
        ranked_chunks = self.retrieval_pipeline.search_and_rerank(
            query=query,
            final_top_k=text_top_k,
        )

        chunk_evidence = [
            RerankedChunkEvidence(
                chunk=chunk,
                rerank_score=score,
                rank=idx + 1,
            )
            for idx, (chunk, score) in enumerate(ranked_chunks)
        ]

        # Step 2: Knowledge graph seed matching & k-hop ego sub-graph expansion
        query_terms = self._extract_query_terms(query)
        matched_seeds = self.traverser.find_matching_nodes(query_terms)

        subgraph_dict = self.traverser.extract_subgraph_khop(
            seed_nodes=matched_seeds,
            k_hops=k_hops,
            max_nodes=max_subgraph_nodes,
        )

        # Step 3: Discover relational pathways bidirectionally between pairs of identified seeds
        discovered_paths: List[List[str]] = []
        if len(matched_seeds) >= 2:
            for i in range(len(matched_seeds)):
                for j in range(i + 1, len(matched_seeds)):
                    u, v = matched_seeds[i], matched_seeds[j]
                    paths_forward = self.traverser.find_paths_between(u, v, max_depth=3)
                    paths_backward = self.traverser.find_paths_between(v, u, max_depth=3)
                    
                    for p in paths_forward + paths_backward:
                        if p not in discovered_paths:
                            discovered_paths.append(p)

        # Convert sub-graph data to schema instances
        graph_nodes = [
            GraphNodeEvidence(
                id=node["id"],
                canonical_name=node.get("canonical_name", node["id"]),
                entity_type=node.get("entity_type", "CONCEPT"),
                aliases=node.get("aliases", []),
                description=node.get("description", ""),
                community_id=node.get("community_id"),
                source_chunk_ids=node.get("source_chunk_ids", []),
            )
            for node in subgraph_dict.get("nodes", [])
        ]

        graph_edges = [
            GraphEdgeEvidence(
                source=edge["source"],
                target=edge["target"],
                relation_type=edge.get("relation_type", "RELATES_TO"),
                description=edge.get("description", ""),
                confidence=edge.get("confidence", 1.0),
                source_chunk_id=edge.get("source_chunk_id", ""),
            )
            for edge in subgraph_dict.get("edges", [])
        ]

        subgraph_evidence = SubgraphEvidence(
            nodes=graph_nodes,
            edges=graph_edges,
            seed_entities=matched_seeds,
            paths=discovered_paths,
        )

        return UnifiedEvidencePacket(
            query=query,
            text_chunks=chunk_evidence,
            subgraph=subgraph_evidence,
            metadata={
                "matched_seed_count": len(matched_seeds),
                "total_graph_nodes": len(graph_nodes),
                "total_graph_edges": len(graph_edges),
                "total_text_chunks": len(chunk_evidence),
            },
        )