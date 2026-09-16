from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TalentSync AI"
    environment: str = "development"
    database_url: str = Field(default="sqlite:///./talentsync.db")
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    upload_dir: str = "uploads"
    cv_parser: str = "docling"
    cv_ocr_enabled: bool = True
    cv_ocr_force_full_page: bool = False
    cv_docling_timeout_seconds: float = 120
    cv_docling_min_text_chars: int = 200
    static_dir: str | None = None
    azure_storage_account_url: str | None = None
    azure_storage_container: str = "cvs"
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_long_enough(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
