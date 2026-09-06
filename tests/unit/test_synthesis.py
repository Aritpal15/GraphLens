from unittest.mock import MagicMock
import pytest
from app.evidence.schemas import (
    GraphEdgeEvidence,
    GraphNodeEvidence,
    RerankedChunkEvidence,
    SubgraphEvidence,
    UnifiedEvidencePacket,
)
from app.ingestion.schemas import TextChunk
from app.synthesis.prompts import (
    build_synthesis_prompt,
    format_subgraph_for_prompt,
    format_text_chunks_for_prompt,
)
from app.synthesis.synthesizer import AnswerSynthesizer


@pytest.fixture
def sample_evidence_packet():
    chunk1 = TextChunk(
        chunk_id="doc_k8s_p1_c0",
        doc_id="doc_k8s",
        filename="k8s_arch.pdf",
        page_number=1,
        chunk_index=0,
        token_count=45,
        text="The kubelet reports node metrics and health status to the kube-apiserver periodically.",
        metadata={"page": 1},
    )
    chunk2 = TextChunk(
        chunk_id="doc_k8s_p2_c1",
        doc_id="doc_k8s",
        filename="k8s_arch.pdf",
        page_number=2,
        chunk_index=1,
        token_count=40,
        text="etcd stores cluster state and serves as the persistence engine for kube-apiserver.",
        metadata={"page": 2},
    )

    text_chunks = [
        RerankedChunkEvidence(chunk=chunk1, rerank_score=0.95, rank=1),
        RerankedChunkEvidence(chunk=chunk2, rerank_score=0.88, rank=2),
    ]

    nodes = [
        GraphNodeEvidence(
            id="kubelet",
            canonical_name="Kubelet",
            entity_type="COMPONENT",
            aliases=["node-agent"],
            description="Agent running on node.",
            source_chunk_ids=["doc_k8s_p1_c0"],
        ),
        GraphNodeEvidence(
            id="kube-apiserver",
            canonical_name="kube-apiserver",
            entity_type="SERVICE",
            aliases=["API Server"],
            description="Control plane hub.",
            source_chunk_ids=["doc_k8s_p1_c0", "doc_k8s_p2_c1"],
        ),
        GraphNodeEvidence(
            id="etcd",
            canonical_name="etcd",
            entity_type="COMPONENT",
            aliases=["kv-store"],
            description="State store.",
            source_chunk_ids=["doc_k8s_p2_c1"],
        ),
    ]

    edges = [
        GraphEdgeEvidence(
            source="kubelet",
            target="kube-apiserver",
            relation_type="COMMUNICATES_WITH",
            description="Reports node status over TLS.",
            confidence=0.98,
            source_chunk_id="doc_k8s_p1_c0",
        ),
        GraphEdgeEvidence(
            source="kube-apiserver",
            target="etcd",
            relation_type="MANAGES",
            description="Writes cluster definitions.",
            confidence=0.99,
            source_chunk_id="doc_k8s_p2_c1",
        ),
    ]

    subgraph = SubgraphEvidence(
        nodes=nodes,
        edges=edges,
        seed_entities=["kubelet", "etcd"],
        paths=[["kubelet", "kube-apiserver", "etcd"]],
    )

    return UnifiedEvidencePacket(
        query="Explain how Kubelet state updates reach etcd.",
        text_chunks=text_chunks,
        subgraph=subgraph,
        metadata={"test_mode": True},
    )


def test_prompt_formatting(sample_evidence_packet):
    text_repr = format_text_chunks_for_prompt(sample_evidence_packet)
    assert "[doc_k8s_p1_c0]" in text_repr
    assert "Rank: 1" in text_repr
    assert "k8s_arch.pdf" in text_repr

    graph_repr = format_subgraph_for_prompt(sample_evidence_packet)
    assert "(kubelet) --[COMMUNICATES_WITH]--> (kube-apiserver)" in graph_repr
    assert "kubelet -> kube-apiserver -> etcd" in graph_repr

    full_prompt = build_synthesis_prompt(sample_evidence_packet)
    assert sample_evidence_packet.query in full_prompt
    assert "You are GraphLens" in full_prompt


def test_citation_extraction():
    synthesizer = AnswerSynthesizer(client=MagicMock())
    sample_text = (
        "The Kubelet forwards telemetry [doc_k8s_p1_c0]. "
        "The kube-apiserver then validates and persists it into etcd [doc_k8s_p2_c1]. "
        "A duplicate citation [doc_k8s_p1_c0] must be ignored in deduplication."
    )
    citations = synthesizer._extract_citations(sample_text)
    assert citations == ["doc_k8s_p1_c0", "doc_k8s_p2_c1"]


def test_synthesizer_mock_generation(sample_evidence_packet):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "Kubelet communicates with kube-apiserver to report metrics [doc_k8s_p1_c0]. "
        "In turn, kube-apiserver commits this state into etcd [doc_k8s_p2_c1]."
    )
    mock_client.models.generate_content.return_value = mock_response

    synthesizer = AnswerSynthesizer(client=mock_client)
    result = synthesizer.synthesize(sample_evidence_packet)

    assert result.query == sample_evidence_packet.query
    assert "Kubelet communicates with kube-apiserver" in result.answer
    assert result.cited_chunk_ids == ["doc_k8s_p1_c0", "doc_k8s_p2_c1"]
    assert result.model_used != ""