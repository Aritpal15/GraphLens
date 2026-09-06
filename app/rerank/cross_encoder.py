from typing import List, Tuple
from sentence_transformers import CrossEncoder
from app.config.settings import settings
from app.ingestion.schemas import TextChunk


class CrossEncoderReranker:
    def __init__(self, model_name: str = settings.RERANKER_MODEL_NAME):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        chunks: List[TextChunk],
        top_k: int = 5
    ) -> List[Tuple[TextChunk, float]]:
        if not chunks:
            return []

        # Prepare query-text pairs for cross-attention scoring
        pairs = [[query, chunk.text] for chunk in chunks]
        scores = self.model.predict(pairs)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: float(scores[i]),
            reverse=True
        )[:top_k]

        return [(chunks[i], float(scores[i])) for i in ranked_indices]