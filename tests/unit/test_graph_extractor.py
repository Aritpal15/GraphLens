import json
from unittest.mock import MagicMock
import pytest
from app.graph.extractor import GraphEntityExtractor, RawExtractionPayload
from app.graph.schemas import (
    ChunkExtractionResult,
    EntityType,
    ExtractedEntity,
    ExtractedRelationship,
    RelationType,
)
from app.ingestion.schemas import TextChunk


@pytest.fixture
def sample_chunk():
    return TextChunk(
        chunk_id="doc_test_p1_c0",
        doc_id="doc_test",
        filename="test_arch.pdf",
        page_number=1,
        chunk_index=0,
        token_count=45,
        text="The Kubelet communicates with the kube-apiserver over HTTPS to receive pod manifests.",
        metadata={"page": 1},
    )


@pytest.fixture
def mock_extraction_payload():
    return RawExtractionPayload(
        entities=[
            ExtractedEntity(
                name="Kubelet",
                entity_type=EntityType.COMPONENT,
                aliases=["kubelet agent"],
                description="Node-level agent running containers.",
                source_chunk_id="doc_test_p1_c0",
            ),
            ExtractedEntity(
                name="kube-apiserver",
                entity_type=EntityType.SERVICE,
                aliases=["API Server"],
                description="Cluster control plane front end.",
                source_chunk_id="doc_test_p1_c0",
            ),
        ],
        relationships=[
            ExtractedRelationship(
                source_name="Kubelet",
                target_name="kube-apiserver",
                relation_type=RelationType.COMMUNICATES_WITH,
                description="Polls for pod specs over secured channel.",
                confidence=0.98,
                source_chunk_id="doc_test_p1_c0",
            )
        ],
    )


def test_extractor_cache_hit(tmp_path, sample_chunk, mock_extraction_payload):
    extractor = GraphEntityExtractor(cache_dir=tmp_path)
    cache_file = extractor._get_cache_path(sample_chunk)

    # Pre-populate cache directly
    cached_result = ChunkExtractionResult(
        chunk_id=sample_chunk.chunk_id,
        doc_id=sample_chunk.doc_id,
        entities=mock_extraction_payload.entities,
        relationships=mock_extraction_payload.relationships,
    )
    cache_file.write_text(cached_result.model_dump_json(), encoding="utf-8")

    # Run extraction without initializing client; should hit cache directly
    result = extractor.extract(sample_chunk)

    assert result.chunk_id == sample_chunk.chunk_id
    assert len(result.entities) == 2
    assert result.entities[0].name == "Kubelet"
    assert len(result.relationships) == 1
    assert result.relationships[0].relation_type == RelationType.COMMUNICATES_WITH


def test_extractor_live_and_caching(tmp_path, sample_chunk, mock_extraction_payload):
    extractor = GraphEntityExtractor(cache_dir=tmp_path)
    extractor.client = MagicMock()

    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = mock_extraction_payload.model_dump_json()
    extractor.client.models.generate_content.return_value = mock_response

    result = extractor.extract(sample_chunk)

    # Verify extracted payload
    assert len(result.entities) == 2
    assert result.relationships[0].source_name == "Kubelet"

    # Verify file was written to cache
    cache_file = extractor._get_cache_path(sample_chunk)
    assert cache_file.exists()

    with open(cache_file, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    assert disk_data["chunk_id"] == sample_chunk.chunk_id
    assert len(disk_data["entities"]) == 2