import re
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config.settings import settings
from app.evidence.schemas import UnifiedEvidencePacket
from app.synthesis.prompts import build_synthesis_prompt


class SynthesizedAnswer(BaseModel):
    query: str
    answer: str
    cited_chunk_ids: List[str] = Field(default_factory=list)
    model_used: str = ""
    evidence_metadata: Dict[str, Any] = Field(default_factory=dict)


class AnswerSynthesizer:
    def __init__(self, client: Optional[genai.Client] = None):
        self.client = client or (genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None)

    def _extract_citations(self, answer_text: str) -> List[str]:
        # Matches patterns like [doc_xxx_p1_c0] or [chunk_xxx]
        citations = re.findall(r"\[([A-Za-z0-9_\-\.]+)\]", answer_text)
        # Deduplicate while preserving order
        seen = set()
        unique_citations = []
        for c in citations:
            if c not in seen:
                seen.add(c)
                unique_citations.append(c)
        return unique_citations

    def synthesize(self, packet: UnifiedEvidencePacket) -> SynthesizedAnswer:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not configured in settings or .env")

        prompt = build_synthesis_prompt(packet)
        models_to_try = [settings.GEMINI_MODEL_PRIMARY, settings.GEMINI_MODEL_FALLBACK]

        answer_text = ""
        model_used = ""
        last_error = None

        for model in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                    ),
                )
                if response.text:
                    answer_text = response.text.strip()
                    model_used = model
                    break
            except Exception as e:
                last_error = e
                continue

        if not answer_text:
            raise RuntimeError(f"Synthesis failed across configured models: {last_error}")

        cited_ids = self._extract_citations(answer_text)

        return SynthesizedAnswer(
            query=packet.query,
            answer=answer_text,
            cited_chunk_ids=cited_ids,
            model_used=model_used,
            evidence_metadata=packet.metadata,
        )