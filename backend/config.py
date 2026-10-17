from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    Application settings with environment variable validation.
    Reads from backend/.env or system environment.
    """
    app_name: str = "CareerProof AI API"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Supabase PostgreSQL Configuration
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, alias="SUPABASE_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: Optional[str] = Field(default=None, alias="SUPABASE_JWT_SECRET")

    # LLM Configuration (OpenAI-compatible endpoint, Gemini, Ollama, etc.)
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="gemini-flash-lite-latest", alias="LLM_MODEL")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")

    # GitHub Integration & Phase 8 Automatic Monitoring
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    github_monitoring_enabled: bool = Field(default=True, alias="GITHUB_MONITORING_ENABLED")
    github_poll_interval_seconds: int = Field(default=60, alias="GITHUB_POLL_INTERVAL_SECONDS")
    github_max_files_per_commit: int = Field(default=50, alias="GITHUB_MAX_FILES_PER_COMMIT")

    # CORS configuration
    allowed_origins: str = Field(default="http://localhost:5173", alias="ALLOWED_ORIGINS")

    # ChromaDB & RAG Configuration
    chroma_db_dir: str = Field(default="data/chroma_db", alias="CHROMA_DB_DIR")
    rag_top_k: int = Field(default=4, alias="RAG_TOP_K")
    rag_distance_threshold: float = Field(default=0.85, alias="RAG_DISTANCE_THRESHOLD")

    # PDF Processing & OCR Configuration
    pdf_max_upload_size_mb: int = Field(default=10, alias="PDF_MAX_UPLOAD_SIZE_MB")
    pdf_max_page_count: int = Field(default=30, alias="PDF_MAX_PAGE_COUNT")
    ocr_language: str = Field(default="eng", alias="OCR_LANGUAGE")
    ocr_tesseract_cmd: Optional[str] = Field(default=None, alias="OCR_TESSERACT_CMD")
    ocr_timeout_seconds: int = Field(default=30, alias="OCR_TIMEOUT_SECONDS")
    pdf_min_page_text_chars: int = Field(default=80, alias="PDF_MIN_PAGE_TEXT_CHARS")

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def chroma_db_path(self) -> Path:
        """Resolve persistent ChromaDB storage directory."""
        path = BASE_DIR / self.chroma_db_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-delimited origins or return default local Vite URL."""
        if not self.allowed_origins:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def pdf_max_upload_size_bytes(self) -> int:
        """Maximum PDF upload size in bytes."""
        return self.pdf_max_upload_size_mb * 1024 * 1024


def get_current_github_token() -> Optional[str]:
    """
    Returns the configured GITHUB_TOKEN. Checks environment variables first,
    then parses backend/.env directly on the fly so token updates take effect immediately
    without requiring a server restart.
    """
    import os
    token = os.getenv("GITHUB_TOKEN")
    if token and token.strip() and token.strip() != "your_github_token":
        return token.strip()

    if ENV_PATH.exists():
        try:
            for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and val != "your_github_token":
                        return val
        except Exception:
            pass

    try:
        settings = get_settings()
        if settings.github_token and settings.github_token.strip() != "your_github_token":
            return settings.github_token.strip()
    except Exception:
        pass

    return None


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
