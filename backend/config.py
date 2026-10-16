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

    # Future integrations (reserved for later phases)
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")

    # CORS configuration
    allowed_origins: str = Field(default="http://localhost:5173", alias="ALLOWED_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-delimited origins or return default local Vite URL."""
        if not self.allowed_origins:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
