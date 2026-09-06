import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import networkx as nx
from networkx.algorithms.community import louvain_communities

from app.graph.schemas import ExtractedEntity, ExtractedRelationship


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_entity(self, entity: ExtractedEntity) -> None:
        node_id = entity.name.strip().lower()
        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                canonical_name=entity.name,
                entity_type=entity.entity_type.value,
                aliases=entity.aliases,
                description=entity.description,
                source_chunk_ids=[entity.source_chunk_id],
                community_id=None,
            )
        else:
            # Merge chunk references and aliases
            node_data = self.graph.nodes[node_id]
            if entity.source_chunk_id not in node_data["source_chunk_ids"]:
                node_data["source_chunk_ids"].append(entity.source_chunk_id)
            merged_aliases = set(node_data.get("aliases", [])) | set(entity.aliases)
            node_data["aliases"] = sorted(list(merged_aliases))

    def add_relationship(self, rel: ExtractedRelationship) -> None:
        source_id = rel.source_name.strip().lower()
        target_id = rel.target_name.strip().lower()

        # Add nodes if not already present
        if not self.graph.has_node(source_id):
            self.graph.add_node(
                source_id,
                canonical_name=rel.source_name,
                entity_type="CONCEPT",
                aliases=[],
                description="",
                source_chunk_ids=[rel.source_chunk_id],
                community_id=None,
            )
        if not self.graph.has_node(target_id):
            self.graph.add_node(
                target_id,
                canonical_name=rel.target_name,
                entity_type="CONCEPT",
                aliases=[],
                description="",
                source_chunk_ids=[rel.source_chunk_id],
                community_id=None,
            )

        self.graph.add_edge(
            source_id,
            target_id,
            relation_type=rel.relation_type.value,
            description=rel.description,
            confidence=rel.confidence,
            source_chunk_id=rel.source_chunk_id,
        )

    def populate(
        self,
        entities: List[ExtractedEntity],
        relationships: List[ExtractedRelationship],
    ) -> None:
        for entity in entities:
            self.add_entity(entity)
        for rel in relationships:
            self.add_relationship(rel)
        self.compute_communities()

    def compute_communities(self) -> None:
        if self.graph.number_of_nodes() == 0:
            return

        # Convert to undirected graph for Louvain community detection
        undirected = self.graph.to_undirected()
        communities = louvain_communities(undirected, seed=42)

        for comm_id, members in enumerate(communities):
            for node in members:
                self.graph.nodes[node]["community_id"] = comm_id

    def to_dict(self) -> Dict[str, Any]:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({"id": node_id, **data})

        edges = []
        for u, v, k, data in self.graph.edges(data=True, keys=True):
            edges.append({"source": u, "target": v, "key": k, **data})

        return {"nodes": nodes, "edges": edges}

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: Path) -> "KnowledgeGraph":
        kg = cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for node in data.get("nodes", []):
            node_id = node.pop("id")
            kg.graph.add_node(node_id, **node)

        for edge in data.get("edges", []):
            u = edge.pop("source")
            v = edge.pop("target")
            edge.pop("key", None)
            kg.graph.add_edge(u, v, **edge)

        return kg