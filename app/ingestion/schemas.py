from typing import Any, Dict
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    page_count: int
    file_size_bytes: int
    content_hash: str

class ExtractedPage(BaseModel):
    doc_id: str
    filename: str
    page_number: int
    text: str

class TextChunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
