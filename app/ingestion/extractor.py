import hashlib
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from app.config.settings import settings
from app.ingestion.schemas import DocumentMetadata, ExtractedPage


class PDFExtractor:
    @staticmethod
    def _compute_hash(file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def extract_document(cls, file_path: Path) -> Tuple[DocumentMetadata, List[ExtractedPage]]:
        resolved_path = file_path.resolve()

        if not resolved_path.is_file():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        file_size = resolved_path.stat().st_size
        max_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(f"File size exceeds limit of {settings.MAX_PDF_SIZE_MB}MB")

        content_hash = cls._compute_hash(resolved_path)
        doc_id = f"doc_{content_hash[:12]}"
        pages: List[ExtractedPage] = []

        with fitz.open(resolved_path) as pdf:
            page_count = len(pdf)
            if page_count > settings.MAX_PDF_PAGES:
                raise ValueError(f"PDF page count ({page_count}) exceeds limit of {settings.MAX_PDF_PAGES}")

            for page_idx in range(page_count):
                page = pdf.load_page(page_idx)
                extracted_text = page.get_text("text").strip()
                if extracted_text:
                    pages.append(
                        ExtractedPage(
                            doc_id=doc_id,
                            filename=resolved_path.name,
                            page_number=page_idx + 1,
                            text=extracted_text
                        )
                    )

        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=resolved_path.name,
            page_count=page_count,
            file_size_bytes=file_size,
            content_hash=content_hash
        )

        return metadata, pages