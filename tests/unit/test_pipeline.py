from pathlib import Path
import pytest
from app.config.settings import settings
from app.ingestion.pipeline import IngestionPipeline


def test_ingest_directory_sample_corpus():
    pipeline = IngestionPipeline(target_tokens=400, overlap_tokens=50)
    sample_dir = settings.SAMPLE_DATA_DIR

    pdf_files = list(sample_dir.glob("*.pdf"))
    if not pdf_files:
        pytest.skip("No sample PDFs found in data/sample.")

    metadatas, chunks = pipeline.ingest_directory(sample_dir)

    assert len(metadatas) == len(pdf_files)
    assert len(chunks) > 0

    # Ensure all chunks retain valid provenance metadata
    for chunk in chunks:
        assert chunk.doc_id.startswith("doc_")
        assert chunk.filename.endswith(".pdf")
        assert chunk.page_number >= 1
        assert chunk.token_count > 0
        assert len(chunk.text.strip()) > 0

    # Test idempotency: re-ingesting the directory should not duplicate chunks or docs
    initial_chunk_count = len(chunks)
    re_metadatas, re_chunks = pipeline.ingest_directory(sample_dir)

    assert len(re_metadatas) == len(metadatas)
    assert len(re_chunks) == initial_chunk_count