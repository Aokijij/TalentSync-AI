# ruff: noqa: F811
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.api.schemas.account import EmailRequest
from app.application.use_cases import recommendations
from app.domain.entities.enums import ApplicationStatus, UserRole
from app.domain.services.market_radar import market_report
from app.infrastructure.database.models import (
    Application,
    Company,
    EventLog,
    Job,
    Profile,
    User,
    UserSession,
)
from app.infrastructure.database.session import Base
from app.infrastructure.repositories.profiles import ProfileRepository
from scripts.seed_realistic import replace_old_data, seed


def test_applied_list_includes_every_applicant_below_invitation_threshold(client, monkeypatch):
    _, owner = company_account(client, "counts-owner")
    job = create_job(client, owner)
    for index in range(3):
        user, _ = register(client, f"applicant-{index}", skills=["excel"])
        with client.session_factory() as db:
            db.add(Application(user_id=user["id"], job_id=job["id"], status=[ApplicationStatus.SUBMITTED, ApplicationStatus.REVIEWING, ApplicationStatus.REJECTED][index]))
            db.commit()
    # Use concrete database users while controlling the unrelated scoring model.
    def ranked(db, job, **kwargs):
        users = db.session.query(User).filter(User.role == UserRole.CANDIDATE).all()
        return list(zip(users, [25, 55, 91]))
    monkeypatch.setattr(recommendations, "rank_candidates_for_job", ranked)
    response = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates-page", headers=owner, params={"audience": "applied", "minimum_match": 80})
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 3
    assert client.get(f"/api/v1/jobs/{job['id']}", headers=owner).json()["applications_count"] == 3


def test_certificate_links_and_evidence_are_saved_together(client):
    _, headers = register(client, "credential-owner", skills=["sql"])
    payload = {"title": "Certificado de análisis SQL", "kind": "certificate", "issuer": "Proveedor de formación", "year": "2026", "url": "https://credentials.example.org/SQL-123", "description": "Preparé consultas y documenté los resultados del proyecto final.", "skills": ["sql"], "add_to_profile": True}
    response = client.post("/api/v1/matching/evidence", headers=headers, json=payload)
    assert response.status_code in {200, 201}, response.text
    evidence = response.json()[-1]
    certificate = client.get("/api/v1/profiles/me", headers=headers).json()["certifications"][-1]
    assert certificate["url"] == payload["url"] and certificate["evidence_id"] == evidence["id"]
    assert certificate["issuer"] == payload["issuer"] and certificate["year"] == "2026"
    assert certificate["description"] == payload["description"]
    later = client.post("/api/v1/matching/evidence", headers=headers, json={**payload, "title": "Segundo certificado", "add_to_profile": False}).json()[-1]
    for _ in range(2):
        response = client.post(f"/api/v1/matching/evidence/{later['id']}/skills", headers=headers)
        assert response.status_code == 200, response.text
    saved = client.get("/api/v1/profiles/me", headers=headers).json()["certifications"]
    assert len(saved) == 2 and saved[-1]["url"] == payload["url"]
    for url in ["javascript:alert(1)", "http://credentials.example.org/123", "https://user:secret@credentials.example.org/123"]:
        assert client.put("/api/v1/profiles/me", headers=headers, json={"certifications": [{"name": "Curso", "url": url}]}).status_code == 422
        assert client.post("/api/v1/matching/evidence", headers=headers, json={**payload, "url": url}).status_code == 422


def test_realistic_reset_preserves_admin_personal_profiles_and_builds_usable_market():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        admin = User(name="Administrador", email="admin@example.com", role=UserRole.ADMIN, password_hash="preserve-hash", mfa_secret="preserve-mfa", mfa_enabled=True)
        personal = User(name="Personal", email="personal@correo.co", password_hash="personal-hash", role=UserRole.CANDIDATE)
        scenario = User(name="Escenario", email="scenario@example.com", password_hash="remove", role=UserRole.CANDIDATE)
        db.add_all([admin, personal, scenario]); db.flush()
        db.add(Profile(user_id=personal.id, skills=["mi habilidad"], experience="Conservar información personal"))
        db.add(UserSession(user_id=admin.id, token_hash="keep-session-token", csrf_hash="keep-csrf", expires_at=datetime.utcnow() + timedelta(days=1)))
        db.add(EventLog(actor_user_id=admin.id, event_type="old-scenario-event", entity_type="user", entity_id=scenario.id, details={}))
        db.commit()
        admin_before = tuple(db.execute(select(User.__table__).where(User.id == admin.id)).one())
        session_before = tuple(db.execute(select(UserSession.__table__)).one())
        personal_id = personal.id
        removed = replace_old_data(db)
        assert removed["users"] == 1
        result = seed(db, "Local-test-password!2026")
        db.commit()
        assert all(EmailRequest(email=row["email"]) for row in result["accounts"])
        for account in [row for row in result["accounts"] if row["type"] == "Candidato"]:
            candidate = db.query(User).filter_by(email=account["email"]).one()
            assert len(candidate.applications) == 5
            assert len({row.pipeline_stage for row in candidate.applications}) >= 3
        assert result["jobs"] == 360 and result["companies"] == 30 and result["candidates"] == 105
        assert tuple(db.execute(select(User.__table__).where(User.id == admin.id)).one()) == admin_before
        assert tuple(db.execute(select(UserSession.__table__)).one()) == session_before
        assert not db.query(EventLog).filter_by(event_type="old-scenario-event").count()
        assert db.query(EventLog).filter_by(event_type="application.transition").count() > 0
        assert db.get(User, personal_id).profile.skills == ["mi habilidad"]
        assert db.query(Application).count() == result["applications"] == 720
        assert len({job.location for job in db.query(Job)}) >= 12
        assert len({job.sector for job in db.query(Job)}) >= 12
        assert all(len({job.quality_summary["score"] for job in company.jobs}) >= 3 for company in db.query(Company))
        assert all(not job.blind_hiring for job in db.query(Job))
        profile = db.query(Profile).filter(Profile.preferences["local_fixture"].as_boolean().is_(True)).first()
        filters = {"family": "software", "level": "junior", "location": "Medellín", "allow_local_fixtures": True}
        peers = ProfileRepository(db, Profile).market_participants("software", "junior")
        report = market_report(profile, db.query(Job).all(), peers, [], filters)
        assert report["demand"]["sample"] >= 30 and report["demand"]["own_skills"]
        assert report["peers"]["status"] == "ready" and report["peers"]["sample"] == 29
        assert report["salary"]["status"] == "ready" and report["salary"]["groups"][0]["sample"] == 30
        assert report["available_cohorts"] and report["local_data"]
        real = market_report(profile, db.query(Job).all(), peers, [], {**filters, "allow_local_fixtures": False})
        assert real["demand"]["sample"] == 0 and real["peers"]["status"] == "insufficient_data"
        assert not db.connection().exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    engine.dispose()
