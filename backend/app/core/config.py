from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    APP_NAME: str = "DataFlow Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://dataflow:dataflow@localhost:5432/dataflow"
    DATABASE_URL_SYNC: str = "postgresql://dataflow:dataflow@localhost:5432/dataflow"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Security
    SECRET_KEY: str = "change-me-in-production-at-least-32-chars"
    SECRET_ENCRYPTION_KEY: str = ""  # Fernet key (base64 32 bytes) — generated on first run
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # File Upload
    MAX_FILE_SIZE_MB: int = 100
    UPLOAD_DIR: str = "/tmp/dataflow_uploads"

    # Default admin (seeded on startup)
    FIRST_ADMIN_EMAIL: str = "admin@dataflow.local"
    FIRST_ADMIN_PASSWORD: str = "Admin123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
