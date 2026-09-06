from typing import List, Tuple
from app.ingestion.schemas import TextChunk
from app.retrieval.bm25_index import BM25Index
from app.retrieval.faiss_index import FAISSIndex
from app.retrieval.hybrid_rrf import HybridRetriever
from app.rerank.cross_encoder import CrossEncoderReranker


class RetrievalPipeline:
    def __init__(
        self,
        rrf_k: int = 60,
        embedding_model: str | None = None,
        reranker_model: str | None = None
    ):
        self.bm25_index = BM25Index()
        self.faiss_index = FAISSIndex() if embedding_model is None else FAISSIndex(model_name=embedding_model)
        self.retriever = HybridRetriever(
            bm25_index=self.bm25_index,
            faiss_index=self.faiss_index,
            rrf_k=rrf_k
        )
        self.reranker = CrossEncoderReranker() if reranker_model is None else CrossEncoderReranker(model_name=reranker_model)
        self.is_indexed = False

    def index_chunks(self, chunks: List[TextChunk]) -> None:
        if not chunks:
            return
        self.bm25_index.index_chunks(chunks)
        self.faiss_index.index_chunks(chunks)
        self.is_indexed = True

    def search_and_rerank(
        self,
        query: str,
        dense_top_k: int = 20,
        sparse_top_k: int = 20,
        rrf_top_k: int = 15,
        final_top_k: int = 5
    ) -> List[Tuple[TextChunk, float]]:
        if not self.is_indexed:
            return []

        # Step 1: Phase 2 Hybrid RRF retrieval
        hybrid_candidates = self.retriever.retrieve(
            query=query,
            dense_top_k=dense_top_k,
            sparse_top_k=sparse_top_k,
            final_top_k=rrf_top_k
        )

        candidate_chunks = [chunk for chunk, _score in hybrid_candidates]

        # Step 2: Phase 3 Cross-Encoder reranking
        reranked_results = self.reranker.rerank(
            query=query,
            chunks=candidate_chunks,
            top_k=final_top_k
        )

        return reranked_results