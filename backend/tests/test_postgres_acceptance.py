"""Opt-in acceptance against migrations in a dedicated loopback PostgreSQL cluster."""
# ruff: noqa: F811
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import test_local_acceptance as journey
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.limiter import limiter
from app.infrastructure.database import session as database_session
from app.infrastructure.database.models import MailMessage
from app.infrastructure.database.session import get_db
from app.main import create_app


@pytest.fixture
def browser(monkeypatch):
    database = os.environ.get("TALENTSYNC_REHEARSAL_DATABASE")
    if not database:
        pytest.skip("Ejecutar mediante scripts/staging_postgres.py check")
    expected = Path(__file__).resolve().parents[2] / ".local/staging/pgdata"
    if Path(os.environ.get("TALENTSYNC_REHEARSAL_DATA", "")).resolve() != expected.resolve():
        pytest.fail("Directorio de ensayo inválido")
    url = make_url(settings.database_url)
    assert url.host == "127.0.0.1" and url.port == 55432
    assert url.database == database and database.startswith("talentsync_rehearsal_")
    engine = create_engine(url)
    # No create_all: this test must use the actual Alembic schema.
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM users")).scalar_one() == 0
        assert connection.execute(text("SELECT current_user")).scalar_one() == "talentsync_rehearsal_app"
    session_factory = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(database_session, "SessionLocal", session_factory)
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "session_auth_enabled", True)
    monkeypatch.setattr(settings, "session_cookie_secure", False)
    # This only creates synthetic outbox rows; PostgreSQL never exposes /dev/mailbox.
    monkeypatch.setattr(settings, "local_mail_enabled", True)
    monkeypatch.setattr(limiter, "enabled", False)

    def test_database():
        with session_factory() as session:
            yield session

    def confirm_synthetic_mail(actor, email):
        with session_factory() as session:
            message = session.query(MailMessage).filter_by(recipient=email).order_by(MailMessage.id.desc()).first()
            assert message is not None
            link = re.search(r"https?://\S+", message.body).group()
        token = parse_qs(urlsplit(link).query)["token"][0]
        journey.request(actor, "POST", "/auth/action/confirm", json={"purpose": "verify", "token": token})

    monkeypatch.setattr(journey, "confirm_mail", confirm_synthetic_mail)
    app = create_app()
    app.dependency_overrides[get_db] = test_database
    try:
        with TestClient(app) as client:
            client.session_factory = session_factory
            assert client.get("/api/v1/dev/mailbox").status_code == 404
            yield client
    finally:
        engine.dispose()


def test_postgres_journey_uses_migrated_schema_and_real_sessions(browser):
    journey.test_local_journey_connects_all_roles_with_sessions_and_mfa(browser)
