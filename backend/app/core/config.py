import os
import re
from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import (
    EmailStr,
    Field,
    SecretStr,
    TypeAdapter,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TalentSync AI"
    environment: str = "development"
    database_url: str = Field(default="sqlite:///./talentsync.db")
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    session_auth_enabled: bool = False
    company_mfa_required: bool = True
    local_admin_review_enabled: bool = False
    local_mfa_review_enabled: bool = False
    local_mail_enabled: bool = False
    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_security: Literal["starttls", "ssl"] = "starttls"
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    resend_enabled: bool = False
    resend_api_key: str = ""
    resend_from: str = ""
    resend_webhook_secret: str = ""
    account_cleanup_enabled: bool = True
    account_retention_enabled: bool = False
    account_retention_days: int = Field(default=90, ge=7, le=365)
    mail_event_retention_days: int = Field(default=90, ge=7, le=365)
    learn_enabled: bool = False
    learn_tenant_id: str = ""
    learn_client_id: str = ""
    learn_client_secret: str = ""
    public_learning_refresh_enabled: bool = False
    youtube_learning_enabled: bool = False
    youtube_api_key: str = ""
    youtube_learning_daily_requests: int = Field(default=100, ge=2, le=500)
    session_cookie_secure: bool = True
    public_app_url: str = "http://127.0.0.1:5173"
    oauth_github_client_id: str = ""
    oauth_github_client_secret: str = ""
    oauth_google_client_id: str = ""
    oauth_google_client_secret: str = ""
    calendar_google_client_id: str = ""
    calendar_google_client_secret: str = ""
    calendar_sync_enabled: bool = False
    oauth_linkedin_client_id: str = ""
    oauth_linkedin_client_secret: str = ""
    github_project_analysis_enabled: bool = False
    codewars_enabled: bool = False
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
    cv_entity_model_path: str = ""
    cv_entity_python: str = ""
    cv_entity_timeout_seconds: float = Field(default=120, ge=10, le=180)
    static_dir: str | None = None
    azure_storage_account_url: str | None = None
    azure_storage_container: str = "cvs"
    r2_endpoint_url: str = ""
    r2_bucket: str = ""
    r2_region: Literal["auto"] = "auto"
    r2_access_key_id: SecretStr = SecretStr("")
    r2_secret_access_key: SecretStr = SecretStr("")
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
    career_writer_model: str = ""
    career_writer_executable: str = ""
    career_writer_timeout_seconds: float = Field(default=90, ge=10, le=120)
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
    def valid_private_storage(self):
        values = (self.r2_endpoint_url, self.r2_bucket, self.r2_access_key_id.get_secret_value(), self.r2_secret_access_key.get_secret_value())
        if not any(values):
            return self
        if not all(values) or any(any(char.isspace() for char in value) for value in values):
            raise ValueError("R2 requiere endpoint, bucket y las dos credenciales S3 completos")
        try:
            endpoint = urlsplit(self.r2_endpoint_url)
            valid = (endpoint.scheme == "https" and endpoint.hostname
                     and re.fullmatch(r"[a-f0-9]{32}(?:\.(?:eu|us|fedramp))?\.r2\.cloudflarestorage\.com", endpoint.hostname)
                     and not endpoint.username and not endpoint.password and endpoint.port in {None, 443}
                     and endpoint.path in {"", "/"} and not endpoint.query and not endpoint.fragment)
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("R2 requiere el endpoint S3 HTTPS de tu cuenta, sin bucket ni parámetros")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", self.r2_bucket):
            raise ValueError("El bucket R2 debe tener entre 3 y 63 caracteres: minúsculas, números y guiones")
        if self.azure_storage_account_url:
            raise ValueError("Selecciona un solo almacenamiento privado: R2 o Azure")
        return self

    @model_validator(mode="after")
    def safe_production_configuration(self):
        if self.environment.casefold() != "production":
            return self
        if self.local_mail_enabled or self.local_admin_review_enabled or self.local_mfa_review_enabled:
            raise ValueError("Producción requiere desactivar el correo y las excepciones de desarrollo")
        origin = urlsplit(self.public_app_url)
        if origin.scheme != "https" or not origin.hostname or origin.hostname in {"localhost", "127.0.0.1", "::1"} or origin.username or origin.password or origin.path or origin.query or origin.fragment:
            raise ValueError("Producción requiere PUBLIC_APP_URL como origen HTTPS público sin ruta")
        if not self.session_auth_enabled or not self.session_cookie_secure or not self.company_mfa_required:
            raise ValueError("Producción requiere sesiones seguras y protección de acceso empresarial")
        if not self.allowed_hosts or "*" in self.allowed_hosts or any(host in {"localhost", "127.0.0.1"} for host in self.allowed_hosts):
            raise ValueError("Producción requiere hosts explícitos")
        if not self.cors_origins or any(urlsplit(value).scheme != "https" or urlsplit(value).hostname in {"localhost", "127.0.0.1", "::1"} for value in self.cors_origins):
            raise ValueError("Producción requiere orígenes CORS HTTPS explícitos")
        database = urlsplit(self.database_url)
        if database.scheme not in {"postgresql", "postgresql+psycopg"} or not database.hostname or parse_qs(database.query).get("sslmode") not in [["require"], ["verify-full"]]:
            raise ValueError("Producción requiere PostgreSQL con TLS")
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
        if self.calendar_sync_enabled and (not self.session_auth_enabled or not self.calendar_google_client_id or not self.calendar_google_client_secret):
            raise ValueError("Google Calendar requiere sesión de navegador y credenciales OAuth propias")
        if self.resend_enabled:
            if self.smtp_enabled or self.local_mail_enabled:
                raise ValueError("Selecciona un solo transporte de correo: local, SMTP o Resend")
            if not self.resend_api_key or any(char.isspace() for char in self.resend_api_key):
                raise ValueError("Resend requiere una clave API válida")
            TypeAdapter(EmailStr).validate_python(self.resend_from)
        if self.learn_enabled:
            from uuid import UUID
            try:
                UUID(self.learn_tenant_id)
                UUID(self.learn_client_id)
            except ValueError:
                raise ValueError("Microsoft Learn requiere identificadores UUID de tenant y aplicación") from None
            if not self.learn_client_secret:
                raise ValueError("Microsoft Learn requiere el secreto de la aplicación")
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
    def mfa_review_active(self):
        return (self.local_mfa_review_enabled and self.environment == "development"
                and self.database_url.startswith("sqlite:"))

    @property
    def admin_mfa_required(self):
        return not self.mfa_review_active and not (self.local_admin_review_enabled and self.environment == "development"
                    and self.database_url.startswith("sqlite:"))

    @property
    def mail_delivery_enabled(self):
        return self.local_mail_enabled or self.smtp_enabled or self.resend_enabled

    @property
    def mail_delivery_mode(self):
        return "pending" if self.smtp_enabled or self.resend_enabled else "local"

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
