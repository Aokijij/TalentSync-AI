from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_text_analysis
from app.core.config import settings
from app.core.limiter import limiter
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import User
from app.infrastructure.database.session import Base, get_db
from app.infrastructure.nlp import resumes
from app.infrastructure.security.jwt import create_access_token
from app.main import create_app


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)

    def test_database():
        with session_factory() as session:
            yield session

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(limiter, "enabled", False)
    app = create_app()
    app.dependency_overrides[get_db] = test_database
    with TestClient(app) as test_client:
        test_client.session_factory = session_factory
        yield test_client
    engine.dispose()


def register(client, name, role="candidate", **fields):
    payload = {
        "name": name,
        "email": f"{name}@example.com",
        "password": "Test-password-2026!",
        "role": role,
        **fields,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    user = response.json()
    token = create_access_token(str(user["id"]), role)
    return user, {"Authorization": f"Bearer {token}"}


def create_job(client, headers):
    response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": "Desarrollador Python",
            "description": "Desarrollo de APIs con Python y SQL",
            "requirements": "Experiencia en Python, SQL y FastAPI",
            "sector": "Tecnologia y software",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def company_account(client, name="empresa"):
    return register(client, name, "company", company_name=name, nit=f"900-{name}")


def test_authentication_and_permissions(client):
    user, headers = register(client, "candidato")
    assert client.get("/api/v1/auth/me", headers=headers).json()["id"] == user["id"]
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/admin/stats", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": user["email"], "password": "wrong"}
        ).status_code
        == 401
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": "Test-password-2026!"}
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert (
        client.post(
            "/api/v1/auth/register",
            json={
                "name": "candidato",
                "email": user["email"],
                "password": "Test-password-2026!",
            },
        ).status_code
        == 409
    )


def test_company_job_crud_and_ownership(client):
    _, owner = company_account(client)
    _, outsider = company_account(client, "otraempresa")
    job = create_job(client, owner)
    assert client.get(f"/api/v1/jobs/{job['id']}").json()["company_name"] == "empresa"
    assert len(client.get("/api/v1/jobs?search=Python").json()) == 1
    assert client.get("/api/v1/jobs?search=inexistente").json() == []
    assert (
        client.patch(
            f"/api/v1/jobs/{job['id']}", headers=outsider, json={"title": "Otro título"}
        ).status_code
        == 403
    )
    updated = client.patch(
        f"/api/v1/jobs/{job['id']}", headers=owner, json={"status": "closed"}
    )
    assert updated.status_code == 200
    assert client.get("/api/v1/jobs").json() == []
    assert len(client.get("/api/v1/jobs?status=closed").json()) == 1
    assert (
        client.put(
            "/api/v1/companies/me",
            headers=owner,
            json={"description": "Empresa actualizada"},
        ).status_code
        == 200
    )
    assert (
        client.get("/api/v1/companies/me", headers=owner).json()["description"]
        == "Empresa actualizada"
    )
    assert client.delete(f"/api/v1/jobs/{job['id']}", headers=owner).status_code == 204
    assert client.get(f"/api/v1/jobs/{job['id']}").status_code == 404


def test_application_pipeline_notifications_and_candidate_access(client):
    _, owner = company_account(client)
    _, outsider = company_account(client, "otraempresa")
    candidate, headers = register(client, "candidato")
    job = create_job(client, owner)
    profile_url = f"/api/v1/profiles/candidates/{candidate['id']}"
    assert client.get(profile_url, headers=owner).status_code == 403
    response = client.post(
        "/api/v1/applications", headers=headers, json={"job_id": job["id"]}
    )
    assert response.status_code == 201, response.text
    application = response.json()
    repeated = client.post(
        "/api/v1/applications", headers=headers, json={"job_id": job["id"]}
    )
    assert repeated.json()["id"] == application["id"]
    assert client.get(profile_url, headers=owner).status_code == 200
    assert client.get(profile_url, headers=outsider).status_code == 403
    assert (
        client.get(
            f"/api/v1/applications/jobs/{job['id']}", headers=outsider
        ).status_code
        == 403
    )
    assert client.put(
        f"/api/v1/applications/jobs/{job['id']}/mark-seen", headers=owner
    ).json() == {"updated": 1}
    application_url = f"/api/v1/applications/{application['id']}/status"
    assert (
        client.put(
            application_url, headers=owner, json={"pipeline_stage": "inexistente"}
        ).status_code
        == 422
    )
    updated = client.put(
        application_url, headers=owner, json={"pipeline_stage": "shortlisted"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "shortlisted"
    stages = [stage for stage in job["pipeline_stages"] if stage["id"] != "shortlisted"]
    assert (
        client.patch(
            f"/api/v1/jobs/{job['id']}", headers=owner, json={"pipeline_stages": stages}
        ).status_code
        == 422
    )
    notifications = client.get("/api/v1/notifications", headers=headers).json()
    assert len(notifications) == 1
    assert notifications[0]["action_url"] == f"/postulaciones?focus={application['id']}"
    assert client.get("/api/v1/notifications/unread-count", headers=headers).json() == {
        "count": 1
    }
    assert (
        client.put(
            f"/api/v1/notifications/{notifications[0]['id']}/read", headers=owner
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"/api/v1/notifications/{notifications[0]['id']}/read", headers=headers
        ).status_code
        == 200
    )
    assert client.get("/api/v1/notifications", headers=headers).json() == []
    assert client.put("/api/v1/notifications/read-all", headers=owner).json() == {
        "ok": True
    }
    assert (
        client.delete(
            f"/api/v1/applications/{application['id']}", headers=headers
        ).status_code
        == 204
    )


def test_profile_and_matching_contract(client):
    _, owner = company_account(client)
    candidate, headers = register(client, "candidato")
    job = create_job(client, owner)
    response = client.put(
        "/api/v1/profiles/me",
        headers=headers,
        json={
            "profession": "Desarrollador Python",
            "skills": ["Python", "SQL", "FastAPI"],
            "experience": "Desarrollo de APIs con Python y SQL",
            "location": "Bogotá",
        },
    )
    assert response.status_code == 200, response.text
    match = client.post(f"/api/v1/jobs/{job['id']}/match", headers=headers)
    assert match.status_code == 200, match.text
    result = match.json()
    assert result["match_percentage"] == round(
        result["skill_match_percentage"] * 0.6
        + result["semantic_match_percentage"] * 0.4,
        2,
    )
    assert result["reasons"][0].startswith("categoria:")
    assert any(reason.startswith("score:skills:") for reason in result["reasons"])
    assert (
        client.get(
            "/api/v1/recommendations/me/jobs?include_all=true", headers=headers
        ).json()[0]["id"]
        == result["id"]
    )
    client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]})
    ranked = client.get(
        f"/api/v1/recommendations/jobs/{job['id']}/candidates", headers=owner
    )
    assert ranked.status_code == 200, ranked.text
    assert ranked.json()[0]["user_id"] == candidate["id"]
    assert ranked.json()[0]["has_applied"] is True


def test_cv_rejects_invalid_uploads_without_overwriting_profile(
    client, monkeypatch, tmp_path
):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    _, headers = register(client, "candidato", profession="Ingeniera")
    for filename, content, content_type in [
        ("cv.txt", b"text", "text/plain"),
        ("cv.pdf", b"", "application/pdf"),
        ("cv.pdf", b"x" * (5 * 1024 * 1024 + 1), "application/pdf"),
    ]:
        response = client.post(
            "/api/v1/profiles/me/cv",
            headers=headers,
            files={"file": (filename, content, content_type)},
        )
        assert response.status_code == 400, response.text
    assert (
        client.get("/api/v1/profiles/me", headers=headers).json()["profession"]
        == "Ingeniera"
    )


def test_cv_enrichment_preserves_curated_fields(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    user, headers = register(
        client,
        "candidato",
        profession="Ingeniera",
        skills=["SQL"],
        experience="Experiencia revisada",
    )
    monkeypatch.setattr(resumes, "extract_pdf_text", lambda path: "Contenido del CV")
    result = SimpleNamespace(
        clean_text="contenido del cv",
        profession=None,
        skills=["Python"],
        experience=None,
        education=None,
        location="Bogotá, Cundinamarca",
        phone=None,
        experiences=[],
        educations=[],
        certifications=[],
        embedding=[1.0, 0.0],
    )
    client.app.dependency_overrides[get_text_analysis] = lambda: SimpleNamespace(
        analyze_cv=lambda text: result
    )
    response = client.post(
        "/api/v1/profiles/me/cv",
        headers=headers,
        files={"file": ("mi cv.pdf", b"%PDF-test", "application/pdf")},
    )
    assert response.status_code == 200, response.text
    profile = response.json()
    assert profile["profession"] == "Ingeniera"
    assert profile["experience"] == "Experiencia revisada"
    assert profile["skills"] == ["sql", "python"]
    assert profile["location"] == "Bogotá"
    assert profile["department"] == "Cundinamarca"
    assert profile["cv_filename"] == "mi_cv.pdf"
    assert (tmp_path / f"user_{user['id']}_mi_cv.pdf").read_bytes() == b"%PDF-test"


def test_admin_overview_and_deletion(client):
    user, _ = register(client, "administrador")
    with client.session_factory() as session:
        session.get(User, user["id"]).role = UserRole.ADMIN
        session.commit()
    headers = {
        "Authorization": f"Bearer {create_access_token(str(user['id']), 'admin')}"
    }
    candidate, _ = register(client, "candidato")
    assert client.get("/api/v1/admin/stats", headers=headers).json()["users"] == 2
    assert (
        len(client.get("/api/v1/admin/analytics", headers=headers).json()["timeline"])
        == 14
    )
    assert len(client.get("/api/v1/admin/users", headers=headers).json()) == 2
    assert client.get("/api/v1/admin/companies", headers=headers).json() == []
    assert client.get("/api/v1/admin/jobs", headers=headers).json() == []
    assert (
        client.delete(f"/api/v1/admin/users/{user['id']}", headers=headers).status_code
        == 400
    )
    assert (
        client.delete(
            f"/api/v1/admin/users/{candidate['id']}", headers=headers
        ).status_code
        == 204
    )
