from pathlib import Path
import pytest
from app.config.settings import settings
from app.ingestion.extractor import PDFExtractor
from app.ingestion.chunker import PageAwareChunker


@pytest.fixture
def sample_pdf_path() -> Path:
    sample_files = list(settings.SAMPLE_DATA_DIR.glob("*.pdf"))
    if not sample_files:
        pytest.skip("No sample PDFs found in data/sample to run ingestion tests.")
    return sample_files[0]


def test_pdf_extraction_metadata_and_pages(sample_pdf_path: Path):
    metadata, pages = PDFExtractor.extract_document(sample_pdf_path)

    assert metadata.doc_id.startswith("doc_")
    assert metadata.filename == sample_pdf_path.name
    assert metadata.page_count > 0
    assert metadata.file_size_bytes > 0
    assert len(metadata.content_hash) == 64  # SHA-256 string length

    assert len(pages) == metadata.page_count
    assert all(page.doc_id == metadata.doc_id for page in pages)
    assert all(page.page_number >= 1 for page in pages)
    assert all(len(page.text.strip()) > 0 for page in pages)


def test_page_aware_chunker_provenance(sample_pdf_path: Path):
    metadata, pages = PDFExtractor.extract_document(sample_pdf_path)
    chunker = PageAwareChunker(target_tokens=300, overlap_tokens=40)
    chunks = chunker.chunk_document(pages)

    assert len(chunks) >= len(pages)
    for chunk in chunks:
        assert chunk.doc_id == metadata.doc_id
        assert chunk.filename == metadata.filename
        assert chunk.page_number >= 1
        assert chunk.chunk_id.startswith(f"{metadata.doc_id}_p{chunk.page_number}_c")
        assert chunk.token_count > 0
        assert len(chunk.text.strip()) > 0
        assert chunk.metadata["page"] == chunk.page_number


def test_extractor_file_not_found():
    with pytest.raises(FileNotFoundError):
        PDFExtractor.extract_document(Path("non_existent_file.pdf"))