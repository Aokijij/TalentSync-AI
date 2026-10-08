import os
from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TalentSync AI"
    environment: str = "development"
    database_url: str = Field(default="sqlite:///./talentsync.db")
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    session_auth_enabled: bool = False
    local_mail_enabled: bool = False
    session_cookie_secure: bool = True
    public_app_url: str = "http://127.0.0.1:5173"
    oauth_github_client_id: str = ""
    oauth_github_client_secret: str = ""
    oauth_google_client_id: str = ""
    oauth_google_client_secret: str = ""
    oauth_linkedin_client_id: str = ""
    oauth_linkedin_client_secret: str = ""
    github_project_analysis_enabled: bool = False
    oauth_workspace_client_id: str = ""
    oauth_workspace_client_secret: str = ""
    workspace_domain: str = ""
    admin_sso_required: bool = False
    admin_sso_provider: Literal["workspace", "entra"] = "workspace"
    entra_tenant_id: str = ""
    oauth_entra_client_id: str = ""
    oauth_entra_client_secret: str = ""
    webrtc_stun_urls: list[str] = Field(default_factory=list, max_length=4)
    webrtc_turn_urls: list[str] = Field(default_factory=list, max_length=4)
    webrtc_turn_secret: str = ""
    webrtc_relay_only: bool = False
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
    workflow_maintenance_enabled: bool = False
    model_maintenance_enabled: bool = False
    match_model_path: str = ""
    match_model_cpu_threads: int = Field(default=2, ge=1, le=8)
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

    @field_validator("webrtc_stun_urls", "webrtc_turn_urls")
    @classmethod
    def valid_ice_urls(cls, values, info):
        allowed = {"stun", "stuns"} if info.field_name == "webrtc_stun_urls" else {"turn", "turns"}
        for value in values:
            try:
                scheme, target = value.split(":", 1)
                parsed = urlsplit(f"//{target}")
                if (scheme not in allowed or len(value) > 250 or not parsed.hostname or parsed.path
                        or parsed.username or parsed.password or parsed.fragment or any(char.isspace() for char in value)
                        or parsed.query not in {"", "transport=udp", "transport=tcp"}
                        or parsed.port is not None and not 1 <= parsed.port <= 65535):
                    raise ValueError()
                if scheme.startswith("stun") and parsed.query:
                    raise ValueError()
            except ValueError:
                raise ValueError("URL ICE inválida; usa stun:servidor:puerto o turn:servidor:puerto?transport=udp, sin credenciales") from None
        return values

    @model_validator(mode="after")
    def valid_turn_configuration(self):
        if self.webrtc_turn_urls and len(self.webrtc_turn_secret) < 32:
            raise ValueError("TURN requiere un secreto compartido de al menos 32 caracteres")
        if self.webrtc_relay_only and not self.webrtc_turn_urls:
            raise ValueError("El modo relay requiere un servidor TURN configurado")
        return self

    @field_validator("catalog_max_age_days", "catalog_min_skills")
    @classmethod
    def positive_catalog_limits(cls, v):
        if v < 1:
            raise ValueError("Los límites del catálogo deben ser mayores que cero")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=os.environ.get("TALENTSYNC_ENV_FILE", ".env"))


settings = get_settings()
