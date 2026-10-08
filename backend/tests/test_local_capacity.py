"""Small concurrent rehearsal on its own SQLite file, never the demo database."""
import json
import os
import statistics
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.limiter import limiter
from app.domain.entities.enums import UserRole
from app.infrastructure.database import session as database_session
from app.infrastructure.database.models import Company, Job, Profile, User
from app.infrastructure.database.session import Base, get_db
from app.infrastructure.security.passwords import hash_password
from app.main import create_app


def test_concurrent_candidates_keep_sessions_and_writes_isolated(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'capacity.sqlite3').as_posix()}",
                           connect_args={"check_same_thread": False, "timeout": 15})
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(database_session, "SessionLocal", factory)
    for name, value in {"database_url": str(engine.url), "session_auth_enabled": True,
                        "session_cookie_secure": False, "local_mail_enabled": False,
                        "smtp_enabled": False, "workflow_maintenance_enabled": False,
                        "model_maintenance_enabled": False, "match_model_path": ""}.items():
        monkeypatch.setattr(settings, name, value)
    monkeypatch.setattr(limiter, "enabled", False)
    password = "Synthetic-load-2026!"
    encoded = hash_password(password)
    with factory() as db:
        owner = User(name="Synthetic company", email="load-owner@example.com", password_hash=encoded, role=UserRole.COMPANY)
        db.add(owner)
        db.flush()
        company = Company(name="Synthetic capacity fixture", nit="CAPACITY-ONLY", owner_user_id=owner.id,
                          verification_status="verified")
        db.add(company)
        db.flush()
        for index in range(50):
            db.add(Job(company_id=company.id, title=f"Python developer {index}", description="Python SQL APIs",
                       requirements="Python SQL", skills=["python", "sql"], status="active", embedding=[]))
        for index in range(8):
            db.add(User(name=f"Synthetic {index}", email=f"load-{index}@example.com", password_hash=encoded,
                        role=UserRole.CANDIDATE, profile=Profile(profession="Python developer", skills=["python"])))
        db.commit()
        job_id = db.query(Job.id).first()[0]
    app = create_app()

    def database():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = database

    def actor(index):
        measurements = []
        with TestClient(app) as client:
            def call(method, path, expected=200, **kwargs):
                started = time.perf_counter()
                response = client.request(method, path, **kwargs)
                measurements.append((response.status_code, (time.perf_counter() - started) * 1000))
                assert response.status_code == expected, (method, path, response.status_code)
                return response

            email = f"load-{index}@example.com"
            call("POST", "/api/v1/auth/session/login", json={"email": email, "password": password})
            csrf = {"X-CSRF-Token": client.cookies.get("talentsync_csrf")}
            for _ in range(2):
                call("GET", "/health")
                profile = call("GET", "/api/v1/profiles/me").json()
                assert profile["profession"] == "Python developer"
                call("GET", "/api/v1/jobs")
                assert len(call("GET", "/api/v1/learning/catalog").json()["assessments"]) == 7
                call("GET", f"/api/v1/matching/jobs/{job_id}")
                call("GET", "/api/v1/admin/stats", 403)
                call("GET", "/api/v1/dev/mailbox", 404)
                call("PUT", "/api/v1/account/privacy", 403, json={"share_evidence": False})
                call("PUT", "/api/v1/account/privacy", headers=csrf,
                     json={"share_evidence": bool(index % 2), "notify_new_skills": False,
                           "personalize_recommendations": True})
        return measurements

    try:
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=8) as workers:
            measurements = [row for group in workers.map(actor, range(8)) for row in group]
        elapsed = time.perf_counter() - started
        with factory() as db:
            for index in range(8):
                user = db.query(User).filter_by(email=f"load-{index}@example.com").one()
                assert user.privacy_preferences["share_evidence"] == bool(index % 2)
        durations = sorted(duration for _, duration in measurements)
        report = {"passed": True, "scope": "synthetic SQLite WAL; in-process ASGI; lexical matching; limiter disabled",
                  "workers": 8, "vacancies": 50, "requests": len(measurements), "seconds": round(elapsed, 3),
                  "requests_per_second": round(len(measurements) / elapsed, 2),
                  "milliseconds": {"median": round(statistics.median(durations), 2),
                                   "p95": round(durations[int(len(durations) * .95) - 1], 2),
                                   "max": round(max(durations), 2)},
                  "status_counts": dict(Counter(status for status, _ in measurements)),
                  "notice": "Local smoke capacity only; not a production SLA or network benchmark."}
        if os.getenv("TALENTSYNC_LOCAL_REHEARSAL") == "1":
            destination = Path(__file__).resolve().parents[2] / ".local/verification"
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "capacity.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    finally:
        engine.dispose()
