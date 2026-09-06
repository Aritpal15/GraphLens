from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.ingestion.schemas import TextChunk


class GraphNodeEvidence(BaseModel):
    id: str
    canonical_name: str
    entity_type: str
    aliases: List[str] = Field(default_factory=list)
    description: str = ""
    community_id: Optional[int] = None
    source_chunk_ids: List[str] = Field(default_factory=list)


class GraphEdgeEvidence(BaseModel):
    source: str
    target: str
    relation_type: str
    description: str = ""
    confidence: float = 1.0
    source_chunk_id: str = ""


class SubgraphEvidence(BaseModel):
    nodes: List[GraphNodeEvidence] = Field(default_factory=list)
    edges: List[GraphEdgeEvidence] = Field(default_factory=list)
    seed_entities: List[str] = Field(default_factory=list)
    paths: List[List[str]] = Field(default_factory=list)


class RerankedChunkEvidence(BaseModel):
    chunk: TextChunk
    rerank_score: float
    rank: int


class UnifiedEvidencePacket(BaseModel):
    query: str
    text_chunks: List[RerankedChunkEvidence] = Field(default_factory=list)
    subgraph: SubgraphEvidence = Field(default_factory=SubgraphEvidence)
    metadata: Dict[str, Any] = Field(default_factory=dict)