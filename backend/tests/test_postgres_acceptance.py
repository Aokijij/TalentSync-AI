"""Opt-in acceptance against migrations in a dedicated loopback PostgreSQL cluster."""
# ruff: noqa: F811
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
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
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
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
    # Two real connections race for one outbox row. No SMTP transport is used.
    with browser.session_factory() as session:
        message = MailMessage(recipient="synthetic@example.com", subject="Concurrency", body="Synthetic", delivery_state="pending")
        session.add(message)
        session.commit()
        message_id = message.id
    now = datetime.utcnow()
    barrier = threading.Barrier(2)

    def claim(lease):
        with browser.session_factory() as session:
            worker = SqlAlchemyUnitOfWork(session)
            barrier.wait(timeout=10)
            selected = worker.accounts.claim_mail(now, lease, now + timedelta(minutes=2))
            worker.commit()
            return selected.id if selected else None

    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [workers.submit(claim, lease) for lease in ["worker-one", "worker-two"]]
        results = [future.result(timeout=20) for future in futures]
    assert sorted(value for value in results if value is not None) == [message_id]
    with browser.session_factory() as session:
        row = session.get(MailMessage, message_id)
        assert row.attempts == 1 and row.delivery_state == "sending"
        old_lease = row.lease_token
    with browser.session_factory() as session:
        worker = SqlAlchemyUnitOfWork(session)
        later = now + timedelta(minutes=3)
        assert worker.accounts.claim_mail(later, "recovered-worker", later + timedelta(minutes=2)).id == message_id
        worker.commit()
        assert not worker.accounts.finish_mail(message_id, old_lease, delivery_state="sent")
        worker.commit()
        assert worker.accounts.finish_mail(message_id, "recovered-worker", delivery_state="sent", body="")
        worker.commit()
