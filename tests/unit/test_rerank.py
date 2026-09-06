import pytest
from app.config.settings import settings
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.bm25_index import BM25Index
from app.retrieval.faiss_index import FAISSIndex
from app.retrieval.hybrid_rrf import HybridRetriever
from app.rerank.cross_encoder import CrossEncoderReranker


@pytest.fixture(scope="module")
def sample_hybrid_chunks():
    sample_dir = settings.SAMPLE_DATA_DIR
    pdf_files = list(sample_dir.glob("*.pdf"))
    if not pdf_files:
        pytest.skip("No sample PDFs found in data/sample to run rerank tests.")

    pipeline = IngestionPipeline(target_tokens=350, overlap_tokens=40)
    _, chunks = pipeline.ingest_directory(sample_dir)

    bm25 = BM25Index()
    bm25.index_chunks(chunks)

    faiss_idx = FAISSIndex()
    faiss_idx.index_chunks(chunks)

    retriever = HybridRetriever(bm25_index=bm25, faiss_index=faiss_idx, rrf_k=60)
    fused_results = retriever.retrieve(
        query="Kubernetes pod scheduling and kube-scheduler architecture",
        dense_top_k=10,
        sparse_top_k=10,
        final_top_k=10
    )
    return [chunk for chunk, _score in fused_results]


def test_cross_encoder_reranking(sample_hybrid_chunks):
    reranker = CrossEncoderReranker()
    query = "Kubernetes pod scheduling and kube-scheduler architecture"

    reranked = reranker.rerank(
        query=query,
        chunks=sample_hybrid_chunks,
        top_k=5
    )

    assert len(reranked) > 0
    assert len(reranked) <= 5

    # Check scores are strictly in descending order
    scores = [score for _, score in reranked]
    assert scores == sorted(scores, reverse=True)

    # Check provenance contract is retained
    top_chunk, _ = reranked[0]
    assert top_chunk.doc_id.startswith("doc_")
    assert top_chunk.filename.endswith(".pdf")
    assert top_chunk.page_number >= 1
    assert top_chunk.token_count > 0


def test_cross_encoder_empty_input():
    reranker = CrossEncoderReranker()
    reranked = reranker.rerank(query="test query", chunks=[], top_k=5)
    assert reranked == []