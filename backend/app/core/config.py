"""
Application configuration.

Loads all configuration from environment variables (via .env locally).
No secrets or credentials are hard-coded here. See docs/security-design.md
and PROJECT_HANDOFF.md for the rules governing secret handling.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "TrustShare API"
    ENVIRONMENT: str = "development"

    # --- Database ---
    DATABASE_URL: str

    # --- Auth / JWT ---
    # Required. Generate a strong random value locally, e.g.:
    #   python -c "import secrets; print(secrets.token_urlsafe(64))"
    # Never hard-code this or commit a real value.
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # --- Object storage (Backblaze B2, S3-compatible) ---
    # Holds ciphertext only — files are AES-256-GCM encrypted before ever
    # being uploaded here. See docs/architecture.md.
    B2_KEY_ID: str
    B2_APPLICATION_KEY: str
    B2_BUCKET_NAME: str
    B2_ENDPOINT_URL: str

    model_config = SettingsConfigDict(
        env_file="../.env",  # repo root .env, one level up from backend/
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. Import and call get_settings() wherever
    configuration is needed instead of instantiating Settings() directly,
    so the .env file is only parsed once per process.
    """
    return Settings()