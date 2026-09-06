import pytest
from app.graph.knowledge_graph import KnowledgeGraph
from app.graph.schemas import (
    EntityType,
    ExtractedEntity,
    ExtractedRelationship,
    RelationType,
)
from app.graph.traversal import GraphTraverser


@pytest.fixture
def populated_traverser():
    kg = KnowledgeGraph()
    entities = [
        ExtractedEntity(
            name="kubelet",
            entity_type=EntityType.COMPONENT,
            aliases=["Node Agent"],
            description="Runs containers on worker node.",
            source_chunk_id="chunk_1",
        ),
        ExtractedEntity(
            name="kube-apiserver",
            entity_type=EntityType.SERVICE,
            aliases=["API Server", "control-plane-api"],
            description="Cluster front-end entrypoint.",
            source_chunk_id="chunk_1",
        ),
        ExtractedEntity(
            name="etcd",
            entity_type=EntityType.COMPONENT,
            aliases=["State Store"],
            description="Consistent distributed key-value store.",
            source_chunk_id="chunk_2",
        ),
        ExtractedEntity(
            name="Prometheus",
            entity_type=EntityType.SERVICE,
            aliases=["Metrics Engine"],
            description="Scrapes operational metrics.",
            source_chunk_id="chunk_3",
        ),
    ]

    relationships = [
        ExtractedRelationship(
            source_name="kubelet",
            target_name="kube-apiserver",
            relation_type=RelationType.COMMUNICATES_WITH,
            description="Watches pod specs via TLS.",
            confidence=0.95,
            source_chunk_id="chunk_1",
        ),
        ExtractedRelationship(
            source_name="kube-apiserver",
            target_name="etcd",
            relation_type=RelationType.MANAGES,
            description="Persists cluster state objects.",
            confidence=0.99,
            source_chunk_id="chunk_2",
        ),
        ExtractedRelationship(
            source_name="Prometheus",
            target_name="kubelet",
            relation_type=RelationType.MEASURES,
            description="Scrapes cAdvisor container metrics.",
            confidence=0.90,
            source_chunk_id="chunk_3",
        ),
    ]

    kg.populate(entities, relationships)
    return GraphTraverser(kg)


def test_find_matching_nodes_direct_and_alias(populated_traverser):
    # Match via canonical name substring
    matches_direct = populated_traverser.find_matching_nodes(["apiserver"])
    assert "kube-apiserver" in matches_direct

    # Match via alias
    matches_alias = populated_traverser.find_matching_nodes(["State Store"])
    assert "etcd" in matches_alias

    # Multiple query terms
    multi_matches = populated_traverser.find_matching_nodes(["kubelet", "Prometheus"])
    assert "kubelet" in multi_matches
    assert "prometheus" in multi_matches


def test_extract_subgraph_khop(populated_traverser):
    # 1-hop expansion around kubelet should capture kubelet, kube-apiserver, and prometheus
    subgraph_1hop = populated_traverser.extract_subgraph_khop(
        seed_nodes=["kubelet"],
        k_hops=1,
        max_nodes=10
    )

    node_ids = {n["id"] for n in subgraph_1hop["nodes"]}
    assert "kubelet" in node_ids
    assert "kube-apiserver" in node_ids
    assert "prometheus" in node_ids
    assert "etcd" not in node_ids  # etcd is 2 hops away from kubelet

    # 2-hop expansion around kubelet should now reach etcd
    subgraph_2hop = populated_traverser.extract_subgraph_khop(
        seed_nodes=["kubelet"],
        k_hops=2,
        max_nodes=10
    )
    node_ids_2hop = {n["id"] for n in subgraph_2hop["nodes"]}
    assert "etcd" in node_ids_2hop


def test_find_paths_between(populated_traverser):
    # Path: Prometheus -> kubelet -> kube-apiserver -> etcd
    paths = populated_traverser.find_paths_between("Prometheus", "etcd", max_depth=3)

    assert len(paths) == 1
    assert paths[0] == ["prometheus", "kubelet", "kube-apiserver", "etcd"]

    # Non-existent path check (reverse direction has no directed edges)
    reverse_paths = populated_traverser.find_paths_between("etcd", "Prometheus", max_depth=3)
    assert reverse_paths == []