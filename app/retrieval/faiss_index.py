from typing import List, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config.settings import settings
from app.ingestion.schemas import TextChunk


class FAISSIndex:
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_embedding_dimension()
        # Inner product index over normalized vectors computes cosine similarity
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks: List[TextChunk] = []

    def index_chunks(self, chunks: List[TextChunk], batch_size: int = 32) -> None:
        if not chunks:
            return

        self.chunks = chunks
        texts = [chunk.text for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype(np.float32)

        self.index.reset()
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[TextChunk, float]]:
        if self.index.ntotal == 0 or not self.chunks:
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype(np.float32)

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, k)

        results: List[Tuple[TextChunk, float]] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1:
                results.append((self.chunks[idx], float(score)))

        return results