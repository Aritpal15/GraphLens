from unittest.mock import MagicMock
import pytest
from app.evidence.assembler import EvidenceAssembler
from app.evidence.schemas import UnifiedEvidencePacket
from app.graph.knowledge_graph import KnowledgeGraph
from app.graph.schemas import (
    EntityType,
    ExtractedEntity,
    ExtractedRelationship,
    RelationType,
)
from app.graph.traversal import GraphTraverser
from app.ingestion.schemas import TextChunk
from app.retrieval.pipeline import RetrievalPipeline


@pytest.fixture
def mock_evidence_components():
    # 1. Mock RetrievalPipeline
    mock_retrieval = MagicMock(spec=RetrievalPipeline)
    sample_chunk = TextChunk(
        chunk_id="chunk_k8s_1",
        doc_id="doc_k8s",
        filename="k8s.pdf",
        page_number=1,
        chunk_index=0,
        token_count=50,
        text="The kubelet reports node metrics directly to the kube-apiserver.",
        metadata={"page": 1},
    )
    mock_retrieval.search_and_rerank.return_value = [(sample_chunk, 0.92)]

    # 2. Populated KnowledgeGraph & GraphTraverser
    kg = KnowledgeGraph()
    entities = [
        ExtractedEntity(
            name="kubelet",
            entity_type=EntityType.COMPONENT,
            aliases=["node agent"],
            description="Node execution agent.",
            source_chunk_id="chunk_k8s_1",
        ),
        ExtractedEntity(
            name="kube-apiserver",
            entity_type=EntityType.SERVICE,
            aliases=["API Server"],
            description="Central control plane server.",
            source_chunk_id="chunk_k8s_1",
        ),
    ]
    relationships = [
        ExtractedRelationship(
            source_name="kubelet",
            target_name="kube-apiserver",
            relation_type=RelationType.COMMUNICATES_WITH,
            description="Reports node heartbeats.",
            confidence=0.97,
            source_chunk_id="chunk_k8s_1",
        )
    ]
    kg.populate(entities, relationships)
    traverser = GraphTraverser(kg)

    return mock_retrieval, traverser


def test_evidence_assembler_query_terms():
    mock_retrieval = MagicMock(spec=RetrievalPipeline)
    mock_traverser = MagicMock(spec=GraphTraverser)
    assembler = EvidenceAssembler(mock_retrieval, mock_traverser)

    terms = assembler._extract_query_terms("How does kubelet interact with kube-apiserver in the cluster?")
    assert "kubelet" in terms
    assert "interact" in terms
    assert "kube-apiserver" in terms
    assert "cluster" in terms
    assert "the" not in terms
    assert "with" not in terms


def test_evidence_assembly_bundle(mock_evidence_components):
    mock_retrieval, traverser = mock_evidence_components
    assembler = EvidenceAssembler(
        retrieval_pipeline=mock_retrieval,
        graph_traverser=traverser,
    )

    query = "How does kubelet communicate with kube-apiserver?"
    packet: UnifiedEvidencePacket = assembler.assemble(
        query=query,
        text_top_k=5,
        k_hops=1,
    )

    # Validate top-level schema
    assert packet.query == query
    assert packet.metadata["total_text_chunks"] == 1
    assert packet.metadata["total_graph_nodes"] == 2
    assert packet.metadata["total_graph_edges"] == 1

    # Validate text evidence payload
    top_chunk = packet.text_chunks[0]
    assert top_chunk.rank == 1
    assert top_chunk.rerank_score == 0.92
    assert top_chunk.chunk.chunk_id == "chunk_k8s_1"

    # Validate sub-graph evidence payload
    node_ids = {n.id for n in packet.subgraph.nodes}
    assert "kubelet" in node_ids
    assert "kube-apiserver" in node_ids

    edge = packet.subgraph.edges[0]
    assert edge.source == "kubelet"
    assert edge.target == "kube-apiserver"
    assert edge.relation_type == "COMMUNICATES_WITH"

    # Validate detected paths between seeds
    assert len(packet.subgraph.paths) >= 1
    assert packet.subgraph.paths[0] == ["kubelet", "kube-apiserver"]