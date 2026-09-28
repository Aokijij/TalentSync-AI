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
    jooble_api_key: str | None = None
    jooble_api_base_url: str = "https://co.jooble.org/api"
    jooble_timeout_seconds: float = 20
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    adzuna_country: str = "us"
    adzuna_api_base_url: str = "https://api.adzuna.com/v1/api/jobs"
    adzuna_timeout_seconds: float = 20
    jsearch_api_key: str | None = None
    jsearch_api_base_url: str = "https://api.openwebninja.com/jsearch/search-v2"
    jsearch_timeout_seconds: float = 25
    catalog_max_age_days: int = 60
    catalog_min_skills: int = 3
    periodic_maintenance_enabled: bool = False
    periodic_maintenance_interval_hours: int = 24
    periodic_maintenance_initial_delay_seconds: int = 90
    catalog_sync_keywords: str = (
        "servicio al cliente,administración y ventas,tecnología e ingeniería"
    )
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

    @field_validator("catalog_max_age_days", "catalog_min_skills")
    @classmethod
    def positive_catalog_limits(cls, v):
        if v < 1:
            raise ValueError("Los límites del catálogo deben ser mayores que cero")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
