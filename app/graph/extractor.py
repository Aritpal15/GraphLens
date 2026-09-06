import hashlib
import json
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config.settings import settings
from app.graph.schemas import ChunkExtractionResult, ExtractedEntity, ExtractedRelationship
from app.ingestion.schemas import TextChunk


class RawExtractionPayload(BaseModel):
    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]


class GraphEntityExtractor:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (settings.BASE_DIR / "data" / "cache" / "graph_extractions")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

    def _get_cache_path(self, chunk: TextChunk) -> Path:
        content_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{chunk.chunk_id}_{content_hash}.json"

    def extract(self, chunk: TextChunk) -> ChunkExtractionResult:
        cache_path = self._get_cache_path(chunk)

        # Return cached extraction if already processed
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ChunkExtractionResult.model_validate(data)

        if not self.client:
            raise ValueError("GEMINI_API_KEY is not configured in settings or .env")

        prompt = f"""
Extract all technical entities and direct relationships mentioned in the following text.
Text Chunk ID: {chunk.chunk_id}
Content:
\"\"\"{chunk.text}\"\"\"

Instructions:
1. For every entity, normalize the name into a clean canonical title (e.g., "Kubernetes API Server", "IAM Role").
2. Assign each entity a valid EntityType (SERVICE, PROTOCOL, COMPONENT, SECURITY_CONTROL, FAILURE_MODE, METRIC, CONCEPT).
3. Assign each relationship a valid RelationType (DEPENDS_ON, COMMUNICATES_WITH, MANAGES, SECURES, TRIGGERS, PART_OF, MITIGATES, MEASURES).
4. Tag each entity and relationship with source_chunk_id="{chunk.chunk_id}".
"""

        # Primary model call with fallback handling
        raw_result = self._call_gemini_with_fallback(prompt)

        result = ChunkExtractionResult(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            entities=raw_result.entities,
            relationships=raw_result.relationships,
        )

        # Write result to cache
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        return result

    def _call_gemini_with_fallback(self, prompt: str) -> RawExtractionPayload:
        models_to_try = [settings.GEMINI_MODEL_PRIMARY, settings.GEMINI_MODEL_FALLBACK]

        last_error = None
        for model in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RawExtractionPayload,
                        temperature=0.1,
                    ),
                )
                if response.text:
                    return RawExtractionPayload.model_validate_json(response.text)
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"Extraction failed across all configured models: {last_error}")