from pathlib import Path
from typing import Dict, List, Tuple
from app.config.settings import settings
from app.ingestion.chunker import PageAwareChunker
from app.ingestion.extractor import PDFExtractor
from app.ingestion.schemas import DocumentMetadata, TextChunk


class IngestionPipeline:
    def __init__(
        self,
        target_tokens: int = settings.CHUNK_TARGET_TOKENS,
        overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS
    ):
        self.chunker = PageAwareChunker(
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens
        )
        self.indexed_docs: Dict[str, DocumentMetadata] = {}
        self.all_chunks: List[TextChunk] = []

    def ingest_file(self, file_path: Path) -> Tuple[DocumentMetadata, List[TextChunk]]:
        metadata, pages = PDFExtractor.extract_document(file_path)

        # Idempotent check: skip re-chunking if content hash already exists
        if metadata.doc_id in self.indexed_docs:
            existing_chunks = [c for c in self.all_chunks if c.doc_id == metadata.doc_id]
            return self.indexed_docs[metadata.doc_id], existing_chunks

        chunks = self.chunker.chunk_document(pages)
        self.indexed_docs[metadata.doc_id] = metadata
        self.all_chunks.extend(chunks)

        return metadata, chunks

    def ingest_directory(self, dir_path: Path) -> Tuple[List[DocumentMetadata], List[TextChunk]]:
        resolved_dir = dir_path.resolve()
        if not resolved_dir.is_dir():
            raise NotADirectoryError(f"Directory not found: {resolved_dir}")

        pdf_files = sorted(resolved_dir.glob("*.pdf"))
        if not pdf_files:
            return [], []

        doc_metadatas: List[DocumentMetadata] = []
        for pdf_file in pdf_files:
            metadata, _ = self.ingest_file(pdf_file)
            doc_metadatas.append(metadata)

        return doc_metadatas, self.all_chunks