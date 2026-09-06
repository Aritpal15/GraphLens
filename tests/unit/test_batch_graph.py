from unittest.mock import MagicMock
import pytest
from app.graph.batch_pipeline import BatchGraphExtractor
from app.graph.extractor import GraphEntityExtractor
from app.graph.schemas import (
    ChunkExtractionResult,
    EntityType,
    ExtractedEntity,
    ExtractedRelationship,
    RelationType,
)
from app.ingestion.schemas import TextChunk


@pytest.fixture
def sample_chunks():
    return [
        TextChunk(
            chunk_id="doc_1_p1_c0",
            doc_id="doc_1",
            filename="arch.pdf",
            page_number=1,
            chunk_index=0,
            token_count=35,
            text="The kube-apiserver manages cluster state via etcd.",
            metadata={"page": 1},
        ),
        TextChunk(
            chunk_id="doc_1_p1_c1",
            doc_id="doc_1",
            filename="arch.pdf",
            page_number=1,
            chunk_index=1,
            token_count=30,
            text="API Server acts as the central gateway for control plane nodes.",
            metadata={"page": 1},
        ),
    ]


def test_batch_graph_extractor_merging(sample_chunks):
    mock_extractor = MagicMock(spec=GraphEntityExtractor)

    # First chunk extraction result
    res1 = ChunkExtractionResult(
        chunk_id="doc_1_p1_c0",
        doc_id="doc_1",
        entities=[
            ExtractedEntity(
                name="kube-apiserver",
                entity_type=EntityType.SERVICE,
                aliases=["API Server"],
                description="Cluster front end service.",
                source_chunk_id="doc_1_p1_c0",
            ),
            ExtractedEntity(
                name="etcd",
                entity_type=EntityType.COMPONENT,
                aliases=["kv-store"],
                description="Consistent datastore.",
                source_chunk_id="doc_1_p1_c0",
            ),
        ],
        relationships=[
            ExtractedRelationship(
                source_name="kube-apiserver",
                target_name="etcd",
                relation_type=RelationType.MANAGES,
                description="Persists cluster data.",
                confidence=0.95,
                source_chunk_id="doc_1_p1_c0",
            )
        ],
    )

    # Second chunk extraction result with duplicate entity name and new alias
    res2 = ChunkExtractionResult(
        chunk_id="doc_1_p1_c1",
        doc_id="doc_1",
        entities=[
            ExtractedEntity(
                name="kube-apiserver",
                entity_type=EntityType.SERVICE,
                aliases=["Kubernetes API"],
                description="Gateway interface.",
                source_chunk_id="doc_1_p1_c1",
            )
        ],
        relationships=[],
    )

    mock_extractor.extract.side_effect = [res1, res2]

    batch_pipeline = BatchGraphExtractor(extractor=mock_extractor)
    entities, relationships, raw_results = batch_pipeline.process_chunks(sample_chunks)

    # Verify results
    assert len(raw_results) == 2
    assert len(entities) == 2  # 'kube-apiserver' and 'etcd'
    assert len(relationships) == 1

    # Verify alias merging on kube-apiserver
    apiserver_entity = next(e for e in entities if e.name == "kube-apiserver")
    assert "API Server" in apiserver_entity.aliases
    assert "Kubernetes API" in apiserver_entity.aliases


def test_batch_graph_extractor_error_handling(sample_chunks):
    mock_extractor = MagicMock(spec=GraphEntityExtractor)
    mock_extractor.extract.side_effect = RuntimeError("Extraction failure")

    batch_pipeline = BatchGraphExtractor(extractor=mock_extractor)
    entities, relationships, raw_results = batch_pipeline.process_chunks(sample_chunks)

    # Pipeline should swallow chunk error and proceed
    assert len(entities) == 0
    assert len(relationships) == 0
    assert len(raw_results) == 0