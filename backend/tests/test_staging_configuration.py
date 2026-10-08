from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.main import create_app


def staging(**overrides):
    values = dict(environment="staging", secret_key="x" * 48, session_auth_enabled=True,
                  session_cookie_secure=True, local_mail_enabled=False,
                  public_app_url="https://stage.example.com", allowed_hosts=["stage.example.com"],
                  cors_origins=["https://stage.example.com"],
                  database_url="postgresql+psycopg://app:placeholder@database.invalid/stage?sslmode=require")
    return Settings(_env_file=None, **(values | overrides))


def test_staging_accepts_same_origin_https_with_postgresql_tls():
    assert staging().environment == "staging"
    assert staging(database_url="postgresql+psycopg://app@database.invalid/stage?sslmode=verify-full").session_auth_enabled


@pytest.mark.parametrize("overrides", [
    {"session_auth_enabled": False}, {"session_cookie_secure": False}, {"local_mail_enabled": True},
    {"public_app_url": "http://stage.example.com"}, {"public_app_url": "https://stage.example.com/"},
    {"public_app_url": "https://user:password@stage.example.com"},
    {"allowed_hosts": ["*"]}, {"cors_origins": ["https://separate.pages.dev"]},
    {"database_url": "sqlite://"}, {"database_url": "postgresql+psycopg://app@db/stage"},
    {"database_url": "postgresql+psycopg://app@db/stage?sslmode=disable"},
    {"database_url": "postgresql+psycopg://app@db/stage?sslmode=require&sslmode=disable"},
])
def test_staging_refuses_insecure_or_cross_origin_settings(overrides):
    with pytest.raises(ValidationError):
        staging(**overrides)


def test_staging_hides_docs_and_adds_hsts(monkeypatch):
    monkeypatch.setattr(settings, "environment", "staging")
    with TestClient(create_app()) as client:
        assert client.get("/health").headers["strict-transport-security"].startswith("max-age=")
        assert client.get("/docs").status_code == 404


def test_build_context_excludes_local_credentials_and_weights():
    root = Path(__file__).resolve().parents[2]
    patterns = set((root / ".dockerignore").read_text(encoding="utf-8").splitlines())
    assert {".local", ".azure", ".tmp", "**/.env", "**/.venv"} <= patterns
    assert not any(pattern.startswith("!") and ".local" in pattern for pattern in patterns)
    assert "--no-access-log" in (root / "Dockerfile").read_text(encoding="utf-8")
