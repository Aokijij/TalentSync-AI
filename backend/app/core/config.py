import os
from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import EmailStr, Field, TypeAdapter, field_validator, model_validator
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
    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_security: Literal["starttls", "ssl"] = "starttls"
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
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

    @model_validator(mode="after")
    def safe_staging_configuration(self):
        if self.environment.casefold() != "staging":
            return self
        origin = urlsplit(self.public_app_url)
        if (origin.scheme != "https" or not origin.hostname or origin.username or origin.password
                or origin.path or origin.query or origin.fragment or origin.port not in {None, 443}):
            raise ValueError("Staging requiere PUBLIC_APP_URL como origen HTTPS sin ruta")
        if not self.session_auth_enabled or not self.session_cookie_secure or self.local_mail_enabled:
            raise ValueError("Staging requiere sesiones seguras y buzón local desactivado")
        if self.allowed_hosts != [origin.hostname] or self.cors_origins != [self.public_app_url]:
            raise ValueError("Staging requiere host explícito y frontend/API del mismo origen")
        database = urlsplit(self.database_url)
        if (database.scheme not in {"postgresql", "postgresql+psycopg"} or not database.hostname
                or parse_qs(database.query).get("sslmode") not in [["require"], ["verify-full"]]):
            raise ValueError("Staging requiere PostgreSQL con TLS")
        return self

    @model_validator(mode="after")
    def safe_smtp_configuration(self):
        if self.smtp_enabled:
            if self.local_mail_enabled:
                raise ValueError("SMTP y el buzón local no pueden activarse simultáneamente")
            if (not self.smtp_host or any(char.isspace() for char in self.smtp_host)
                    or any(char in self.smtp_host for char in "/:@")):
                raise ValueError("SMTP requiere un hostname válido, sin URL o credenciales")
            if bool(self.smtp_username) != bool(self.smtp_password):
                raise ValueError("Configura usuario y contraseña SMTP conjuntamente")
            TypeAdapter(EmailStr).validate_python(self.smtp_from)
        return self

    @property
    def mail_delivery_enabled(self):
        return self.local_mail_enabled or self.smtp_enabled

    @property
    def mail_delivery_mode(self):
        return "pending" if self.smtp_enabled else "local"

    @field_validator("catalog_max_age_days", "catalog_min_skills")
    @classmethod
    def positive_catalog_limits(cls, v):
        if v < 1:
            raise ValueError("Los límites del catálogo deben ser mayores que cero")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", hide_input_in_errors=True)


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=os.environ.get("TALENTSYNC_ENV_FILE", ".env"))


settings = get_settings()
