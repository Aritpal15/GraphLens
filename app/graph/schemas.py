from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    SERVICE = "SERVICE"
    PROTOCOL = "PROTOCOL"
    COMPONENT = "COMPONENT"
    SECURITY_CONTROL = "SECURITY_CONTROL"
    FAILURE_MODE = "FAILURE_MODE"
    METRIC = "METRIC"
    CONCEPT = "CONCEPT"


class RelationType(str, Enum):
    DEPENDS_ON = "DEPENDS_ON"
    COMMUNICATES_WITH = "COMMUNICATES_WITH"
    MANAGES = "MANAGES"
    SECURES = "SECURES"
    TRIGGERS = "TRIGGERS"
    PART_OF = "PART_OF"
    MITIGATES = "MITIGATES"
    MEASURES = "MEASURES"


class ExtractedEntity(BaseModel):
    name: str = Field(description="Canonical normalized name of the entity")
    entity_type: EntityType = Field(description="Categorical entity type")
    aliases: List[str] = Field(default_factory=list, description="Alternative names or abbreviations")
    description: str = Field(description="One-sentence definition or role in context")
    source_chunk_id: str = Field(description="Provenance ID of the chunk containing the mention")


class ExtractedRelationship(BaseModel):
    source_name: str = Field(description="Canonical name of the source entity")
    target_name: str = Field(description="Canonical name of the target entity")
    relation_type: RelationType = Field(description="Categorical relation type")
    description: str = Field(description="Contextual statement describing the interaction")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    source_chunk_id: str = Field(description="Provenance ID of the chunk confirming this relationship")


class ChunkExtractionResult(BaseModel):
    chunk_id: str
    doc_id: str
    entities: List[ExtractedEntity] = Field(default_factory=list)
    relationships: List[ExtractedRelationship] = Field(default_factory=list)