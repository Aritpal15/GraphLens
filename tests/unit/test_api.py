from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.evidence.schemas import UnifiedEvidencePacket
from app.main import app
from app.pipeline import GraphLensPipeline
from app.synthesis.synthesizer import SynthesizedAnswer


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "GraphLens API"


def test_index_status_uninitialized(client):
    # Temporarily remove pipeline to test uninitialized state
    original_pipeline = getattr(app.state, "pipeline", None)
    app.state.pipeline = None

    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["indices_ready"] is False
    assert data["status"] == "uninitialized"

    app.state.pipeline = original_pipeline


def test_query_pipeline_not_ready(client):
    mock_pipeline = MagicMock(spec=GraphLensPipeline)
    mock_pipeline.evidence_assembler = None
    app.state.pipeline = mock_pipeline

    response = client.post(
        "/api/v1/query",
        json={"query": "How does etcd communicate with apiserver?", "text_top_k": 3, "k_hops": 1},
    )
    assert response.status_code == 400
    assert "Pipeline is not ready" in response.json()["detail"]


def test_query_success(client):
    mock_pipeline = MagicMock(spec=GraphLensPipeline)
    mock_pipeline.evidence_assembler = MagicMock()

    mock_evidence = UnifiedEvidencePacket(
        query="What is kubelet?",
        text_chunks=[],
        subgraph={"nodes": [], "edges": [], "seed_entities": [], "paths": []},
        metadata={"total_text_chunks": 0},
    )
    mock_answer = SynthesizedAnswer(
        query="What is kubelet?",
        answer="Kubelet is a primary node agent [chunk_k8s_1].",
        cited_chunk_ids=["chunk_k8s_1"],
        model_used="gemini-2.5-flash",
        evidence_metadata={"total_text_chunks": 0},
    )

    mock_pipeline.query.return_value = (mock_answer, mock_evidence)
    app.state.pipeline = mock_pipeline

    response = client.post(
        "/api/v1/query",
        json={"query": "What is kubelet?", "text_top_k": 3, "k_hops": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "What is kubelet?"
    assert payload["answer"] == "Kubelet is a primary node agent [chunk_k8s_1]."
    assert payload["cited_chunk_ids"] == ["chunk_k8s_1"]
    assert payload["model_used"] == "gemini-2.5-flash"
    assert "evidence" in payload