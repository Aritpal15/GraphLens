import pytest
from app.config.settings import settings
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.bm25_index import BM25Index
from app.retrieval.faiss_index import FAISSIndex
from app.retrieval.hybrid_rrf import HybridRetriever


@pytest.fixture(scope="module")
def ingested_corpus_chunks():
    sample_dir = settings.SAMPLE_DATA_DIR
    pdf_files = list(sample_dir.glob("*.pdf"))
    if not pdf_files:
        pytest.skip("No sample PDFs found in data/sample to run retrieval tests.")

    pipeline = IngestionPipeline(target_tokens=350, overlap_tokens=40)
    _, chunks = pipeline.ingest_directory(sample_dir)
    return chunks


def test_bm25_index_and_search(ingested_corpus_chunks):
    bm25 = BM25Index()
    bm25.index_chunks(ingested_corpus_chunks)

    # Search for a domain term known to exist in the cloud corpus
    results = bm25.search("kubernetes pod scheduling architecture", top_k=5)

    assert len(results) > 0
    top_chunk, score = results[0]
    assert score > 0.0
    assert top_chunk.chunk_id != ""
    assert top_chunk.page_number >= 1


def test_faiss_index_and_search(ingested_corpus_chunks):
    faiss_idx = FAISSIndex()
    faiss_idx.index_chunks(ingested_corpus_chunks)

    results = faiss_idx.search("container network interface and overlay mesh", top_k=5)

    assert len(results) > 0
    top_chunk, score = results[0]
    # Cosine similarity scores with normalized embeddings fall within [-1.0, 1.0]
    assert -1.0 <= score <= 1.0
    assert top_chunk.chunk_id != ""
    assert len(top_chunk.text) > 0


def test_hybrid_rrf_fusion(ingested_corpus_chunks):
    bm25 = BM25Index()
    bm25.index_chunks(ingested_corpus_chunks)

    faiss_idx = FAISSIndex()
    faiss_idx.index_chunks(ingested_corpus_chunks)

    retriever = HybridRetriever(bm25_index=bm25, faiss_index=faiss_idx, rrf_k=60)
    fused_results = retriever.retrieve(
        query="AWS IAM roles and security policies",
        dense_top_k=10,
        sparse_top_k=10,
        final_top_k=5
    )

    assert len(fused_results) > 0
    assert len(fused_results) <= 5

    # Check RRF scores are positive and descending
    scores = [score for _, score in fused_results]
    assert all(s > 0.0 for s in scores)
    assert scores == sorted(scores, reverse=True)

    # Check provenance on fused candidates
    top_chunk, _ = fused_results[0]
    assert top_chunk.doc_id.startswith("doc_")
    assert top_chunk.filename.endswith(".pdf")