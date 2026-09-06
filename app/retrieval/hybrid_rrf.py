from typing import Dict, List, Tuple
from app.ingestion.schemas import TextChunk
from app.retrieval.bm25_index import BM25Index
from app.retrieval.faiss_index import FAISSIndex


class HybridRetriever:
    def __init__(
        self,
        bm25_index: BM25Index,
        faiss_index: FAISSIndex,
        rrf_k: int = 60
    ):
        self.bm25_index = bm25_index
        self.faiss_index = faiss_index
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        dense_top_k: int = 20,
        sparse_top_k: int = 20,
        final_top_k: int = 15
    ) -> List[Tuple[TextChunk, float]]:
        bm25_results = self.bm25_index.search(query, top_k=sparse_top_k)
        faiss_results = self.faiss_index.search(query, top_k=dense_top_k)

        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, TextChunk] = {}

        # Accumulate reciprocal rank scores from BM25
        for rank, (chunk, _score) in enumerate(bm25_results, start=1):
            chunk_id = chunk.chunk_id
            chunk_map[chunk_id] = chunk
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))

        # Accumulate reciprocal rank scores from FAISS
        for rank, (chunk, _score) in enumerate(faiss_results, start=1):
            chunk_id = chunk.chunk_id
            chunk_map[chunk_id] = chunk
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))

        # Sort candidate chunks by accumulated RRF score descending
        sorted_ranked = sorted(
            rrf_scores.items(),
            key=lambda item: item[1],
            reverse=True
        )[:final_top_k]

        return [(chunk_map[chunk_id], score) for chunk_id, score in sorted_ranked]