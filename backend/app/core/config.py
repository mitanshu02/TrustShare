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

    # --- Monitoring / notifications (all optional) ---
    # Only trust X-Forwarded-For when the API sits behind a reverse proxy
    # you control (nginx, ALB...). Leave False for local development,
    # otherwise clients could spoof their IP in audit logs.
    TRUST_PROXY_HEADERS: bool = False

    # Email delivery. If SMTP_HOST is empty, emails are written to the
    # server log instead of being sent (development default).
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "TrustShare <no-reply@trustshare.local>"
    SMTP_USE_TLS: bool = True

    # Background job that raises "link expiring" reminders.
    REMINDER_INTERVAL_MINUTES: int = 15
    EXPIRY_REMINDER_HOURS: int = 24

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