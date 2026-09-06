import re
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from app.ingestion.schemas import TextChunk


class BM25Index:
    def __init__(self):
        self.chunks: List[TextChunk] = []
        self.corpus: List[List[str]] = []
        self.bm25: BM25Okapi | None = None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Lowercase and split on non-alphanumeric characters
        return re.findall(r"\b\w+\b", text.lower())

    def index_chunks(self, chunks: List[TextChunk]) -> None:
        self.chunks = chunks
        self.corpus = [self._tokenize(chunk.text) for chunk in chunks]
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[TextChunk, float]]:
        if not self.bm25 or not self.chunks:
            return []

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []

        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        return [(self.chunks[i], float(scores[i])) for i in ranked_indices if scores[i] > 0.0]