from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IndexStatusResponse(BaseModel):
    indexed_chunks: int = 0
    graph_nodes: int = 0
    graph_edges: int = 0
    indices_ready: bool = False
    status: str = "uninitialized"


class IngestionTriggerResponse(BaseModel):
    status: str
    message: str
    documents_queued: int = 0


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user question or research prompt")
    text_top_k: int = Field(default=3, ge=1, le=20, description="Top text chunks to retrieve")
    k_hops: int = Field(default=1, ge=0, le=3, description="Graph traversal hop depth")


class EvidenceChunk(BaseModel):
    chunk_id: str
    text: str
    doc_id: str
    score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    cited_chunk_ids: List[str] = []
    evidence_chunks: List[EvidenceChunk] = []
    traversal_depth: int = 1
    latency: float = 0.0
    subgraph: Optional[Dict[str, Any]] = None