from pathlib import Path
import pytest
from app.graph.knowledge_graph import KnowledgeGraph
from app.graph.schemas import (
    EntityType,
    ExtractedEntity,
    ExtractedRelationship,
    RelationType,
)


@pytest.fixture
def sample_graph_data():
    entities = [
        ExtractedEntity(
            name="kube-apiserver",
            entity_type=EntityType.SERVICE,
            aliases=["API Server"],
            description="Control plane front-end.",
            source_chunk_id="chunk_1",
        ),
        ExtractedEntity(
            name="etcd",
            entity_type=EntityType.COMPONENT,
            aliases=["KV Store"],
            description="Cluster state database.",
            source_chunk_id="chunk_1",
        ),
        ExtractedEntity(
            name="kubelet",
            entity_type=EntityType.COMPONENT,
            aliases=["Node Agent"],
            description="Executes pods on nodes.",
            source_chunk_id="chunk_2",
        ),
    ]

    relationships = [
        ExtractedRelationship(
            source_name="kube-apiserver",
            target_name="etcd",
            relation_type=RelationType.MANAGES,
            description="Writes cluster state.",
            confidence=0.98,
            source_chunk_id="chunk_1",
        ),
        ExtractedRelationship(
            source_name="kubelet",
            target_name="kube-apiserver",
            relation_type=RelationType.COMMUNICATES_WITH,
            description="Polls for work.",
            confidence=0.95,
            source_chunk_id="chunk_2",
        ),
    ]
    return entities, relationships


def test_populate_and_community_detection(sample_graph_data):
    entities, relationships = sample_graph_data
    kg = KnowledgeGraph()
    kg.populate(entities, relationships)

    # Check node count and normalization
    assert kg.graph.number_of_nodes() == 3
    assert "kube-apiserver" in kg.graph.nodes
    assert "etcd" in kg.graph.nodes
    assert "kubelet" in kg.graph.nodes

    # Check edges
    assert kg.graph.number_of_edges() == 2

    # Check community assignments
    for _, node_data in kg.graph.nodes(data=True):
        assert node_data["community_id"] is not None
        assert isinstance(node_data["community_id"], int)


def test_graph_serialization_roundtrip(tmp_path: Path, sample_graph_data):
    entities, relationships = sample_graph_data
    kg = KnowledgeGraph()
    kg.populate(entities, relationships)

    file_path = tmp_path / "kg_export.json"
    kg.save_json(file_path)
    assert file_path.exists()

    reloaded_kg = KnowledgeGraph.load_json(file_path)
    assert reloaded_kg.graph.number_of_nodes() == kg.graph.number_of_nodes()
    assert reloaded_kg.graph.number_of_edges() == kg.graph.number_of_edges()

    apiserver = reloaded_kg.graph.nodes["kube-apiserver"]
    assert apiserver["canonical_name"] == "kube-apiserver"
    assert apiserver["entity_type"] == "SERVICE"
    assert "API Server" in apiserver["aliases"]