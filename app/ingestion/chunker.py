from typing import List
import tiktoken
from app.config.settings import settings
from app.ingestion.schemas import ExtractedPage, TextChunk


class PageAwareChunker:
    def __init__(
        self,
        target_tokens: int = settings.CHUNK_TARGET_TOKENS,
        overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS,
        encoding_name: str = "cl100k_base"
    ):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.get_encoding(encoding_name)

    def chunk_page(self, page: ExtractedPage) -> List[TextChunk]:
        tokens = self.tokenizer.encode(page.text)
        total_tokens = len(tokens)

        if total_tokens <= self.target_tokens:
            chunk_id = f"{page.doc_id}_p{page.page_number}_c0"
            return [
                TextChunk(
                    chunk_id=chunk_id,
                    doc_id=page.doc_id,
                    filename=page.filename,
                    page_number=page.page_number,
                    chunk_index=0,
                    text=page.text,
                    token_count=total_tokens,
                    metadata={"page": page.page_number}
                )
            ]

        chunks: List[TextChunk] = []
        step = self.target_tokens - self.overlap_tokens
        chunk_idx = 0

        for start_idx in range(0, total_tokens, step):
            end_idx = min(start_idx + self.target_tokens, total_tokens)
            token_slice = tokens[start_idx:end_idx]
            decoded_text = self.tokenizer.decode(token_slice).strip()

            chunk_id = f"{page.doc_id}_p{page.page_number}_c{chunk_idx}"
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    doc_id=page.doc_id,
                    filename=page.filename,
                    page_number=page.page_number,
                    chunk_index=chunk_idx,
                    text=decoded_text,
                    token_count=len(token_slice),
                    metadata={"page": page.page_number}
                )
            )
            chunk_idx += 1

            if end_idx >= total_tokens:
                break

        return chunks

    def chunk_document(self, pages: List[ExtractedPage]) -> List[TextChunk]:
        all_chunks: List[TextChunk] = []
        for page in pages:
            all_chunks.extend(self.chunk_page(page))
        return all_chunks