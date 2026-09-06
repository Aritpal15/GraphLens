from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = ""

    # Model Configuration
    GEMINI_MODEL_PRIMARY: str = "gemini-3.5-flash-lite"
    GEMINI_MODEL_FALLBACK: str = "gemini-3.7-flash"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Ingestion & Chunking Limits
    MAX_PDF_SIZE_MB: int = 25
    MAX_PDF_PAGES: int = 50
    CHUNK_TARGET_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 60

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    SAMPLE_DATA_DIR: Path = BASE_DIR / "data" / "sample"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()