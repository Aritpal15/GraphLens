import logging
from typing import Dict, List, Tuple
from app.graph.extractor import GraphEntityExtractor
from app.graph.schemas import ChunkExtractionResult, ExtractedEntity, ExtractedRelationship
from app.ingestion.schemas import TextChunk

logger = logging.getLogger(__name__)


class BatchGraphExtractor:
    def __init__(self, extractor: GraphEntityExtractor | None = None):
        self.extractor = extractor or GraphEntityExtractor()

    def process_chunks(
        self,
        chunks: List[TextChunk]
    ) -> Tuple[List[ExtractedEntity], List[ExtractedRelationship], List[ChunkExtractionResult]]:
        all_results: List[ChunkExtractionResult] = []
        entity_map: Dict[str, ExtractedEntity] = {}
        relationship_list: List[ExtractedRelationship] = []

        for chunk in chunks:
            try:
                result = self.extractor.extract(chunk)
                all_results.append(result)

                # Merge and canonicalize entities by normalized name
                for entity in result.entities:
                    key = entity.name.strip().lower()
                    if key not in entity_map:
                        entity_map[key] = entity
                    else:
                        existing = entity_map[key]
                        # Merge distinct aliases
                        existing_aliases = set(existing.aliases)
                        new_aliases = set(entity.aliases)
                        existing.aliases = sorted(list(existing_aliases | new_aliases))

                # Aggregate relationships
                for rel in result.relationships:
                    relationship_list.append(rel)

            except Exception as exc:
                logger.error(f"Failed extracting graph elements for chunk {chunk.chunk_id}: {exc}")
                continue

        canonical_entities = list(entity_map.values())
        return canonical_entities, relationship_list, all_results