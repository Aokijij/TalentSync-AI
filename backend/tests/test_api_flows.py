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


def test_administrator_uses_the_separate_login_channel(client):
    admin, _ = register(client, "administrador")
    candidate, _ = register(client, "usuario-normal")
    with client.session_factory() as session:
        stored = session.get(User, admin["id"])
        stored.role = UserRole.ADMIN
        session.commit()

    regular_login = client.post(
        "/api/v1/auth/login",
        json={"email": admin["email"], "password": "Test-password-2026!"},
    )
    assert regular_login.status_code == 403
    admin_login = client.post(
        "/api/v1/auth/admin/login",
        json={"email": admin["email"], "password": "Test-password-2026!"},
    )
    assert admin_login.status_code == 200
    assert client.post(
        "/api/v1/auth/admin/login",
        json={"email": candidate["email"], "password": "Test-password-2026!"},
    ).status_code == 401


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
        application_url, headers=owner, json={"pipeline_stage": "reviewing"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "reviewing"
    stages = [stage for stage in job["pipeline_stages"] if stage["id"] != "reviewing"]
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


@pytest.mark.parametrize("mode", ["continue", "new"])
def test_reopening_covered_vacancy_preserves_history_and_notifications(client, mode):
    _, owner = company_account(client, "reabrir")
    _, outsider = company_account(client, "no-propietaria")
    candidate, candidate_headers = register(client, "persona-reabrir")
    _, second_headers = register(client, "otra-persona-reabrir")
    job = create_job(client, owner)
    application = client.post("/api/v1/applications", headers=candidate_headers, json={"job_id": job["id"]}).json()
    other_application = client.post("/api/v1/applications", headers=second_headers, json={"job_id": job["id"]}).json()
    edited = client.put(f"/api/v1/applications/{application['id']}/status", headers=owner, json={"pipeline_stage": "hired", "recruiter_notes": "Seguimiento que debe conservarse"})
    assert edited.status_code == 200, edited.text
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"status": "filled"}).status_code == 200
    before = client.get("/api/v1/applications/me", headers=candidate_headers).json()
    notifications = client.get("/api/v1/notifications?unread_only=false", headers=candidate_headers).json()
    other_before = client.get("/api/v1/applications/me", headers=second_headers).json()
    other_notifications = client.get("/api/v1/notifications?unread_only=false", headers=second_headers).json()
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"status": "active"}).status_code == 422
    url = f"/api/v1/jobs/{job['id']}/reopen"
    assert client.post(url, headers=outsider, json={"mode": mode}).status_code == 403
    assert client.post(url, headers=owner, json={"mode": "reset"}).status_code == 422
    response = client.post(url, headers=owner, json={"mode": mode})
    assert response.status_code == 200, response.text
    reopened = response.json()
    assert reopened["status"] == "active"
    assert client.get("/api/v1/applications/me", headers=candidate_headers).json() == before
    assert client.get("/api/v1/notifications?unread_only=false", headers=candidate_headers).json() == notifications
    assert client.get("/api/v1/applications/me", headers=second_headers).json() == other_before
    assert client.get("/api/v1/notifications?unread_only=false", headers=second_headers).json() == other_notifications
    if mode == "continue":
        assert reopened["id"] == job["id"]
        assert reopened["applications_count"] == 2
        assert client.post(url, headers=owner, json={"mode": mode}).status_code == 409
        moved = client.put(f"/api/v1/applications/{other_application['id']}/status", headers=owner, json={"pipeline_stage": "reviewing"})
        assert moved.status_code == 200, moved.text
        assert moved.json()["resolution_reason"] is None
        assert moved.json()["status"] == "reviewing"
    else:
        assert reopened["id"] != job["id"]
        assert reopened["applications_count"] == 0
        assert reopened["title"] == job["title"]
        assert client.get(f"/api/v1/jobs/{job['id']}").json()["status"] == "filled"
        assert client.get(f"/api/v1/applications/jobs/{reopened['id']}", headers=owner).json() == []


def test_language_levels_are_saved_and_company_candidate_scores_are_identical(client):
    _, owner = company_account(client, "idiomas")
    candidate, headers = register(client, "persona-idiomas", profession="Desarrollador Python", skills=["Python", "SQL", "FastAPI"], experience="Desarrollo de APIs con Python y SQL")
    job = create_job(client, owner)
    updated = client.patch(f"/api/v1/jobs/{job['id']}", headers=owner, json={"languages": [{"name": "English", "level": "b2"}]})
    assert updated.status_code == 200, updated.text
    assert updated.json()["languages"] == [{"name": "inglés", "level": "B2"}]
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["languages"] = [{"name": "Ingles", "level": "B1"}]
    saved = client.put("/api/v1/profiles/me", headers=headers, json=profile)
    assert saved.status_code == 200, saved.text
    assert saved.json()["languages"] == [{"name": "inglés", "level": "B1"}]
    assert client.get("/api/v1/profiles/me", headers=headers).json()["languages"] == saved.json()["languages"]
    match = client.post(f"/api/v1/jobs/{job['id']}/match", headers=headers).json()
    ranked = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates", headers=owner).json()
    company_score = next(item for item in ranked if item["user_id"] == candidate["id"])
    assert company_score["match_percentage"] == match["match_percentage"]
    assert company_score["languages"] == saved.json()["languages"]
    assert match["language_match_percentage"] == 75
    assert any("Idioma por fortalecer" in reason for reason in match["reasons"])
    recommendations = client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=headers).json()
    assert next(item for item in recommendations if item["job_id"] == job["id"])["match_percentage"] == match["match_percentage"]
    invitation = client.post(f"/api/v1/recommendations/jobs/{job['id']}/candidates/{candidate['id']}/invite", headers=owner)
    assert invitation.status_code == 200, invitation.text
    assert f"{match['match_percentage']:.0f}%" in invitation.json()["body"]
    profile["languages"] = [{"name": "inglés", "level": "not-a-level"}]
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 422
    profile["languages"] = [{"name": "English", "level": "B1"}, {"name": "inglés", "level": "B2"}]
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 422


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


@pytest.mark.parametrize("score,expected_count,invite_status", [(50, 1, 200), (49.99, 0, 422)])
def test_talent_search_and_invitations_start_at_fifty_percent(client, monkeypatch, score, expected_count, invite_status):
    from app.application.use_cases import recommendations

    _, owner = company_account(client, "empresa-cincuenta")
    candidate, _ = register(client, "candidato-cincuenta", profession="Analista", skills=["SQL"])
    job = create_job(client, owner)
    monkeypatch.setattr(recommendations, "rank_candidates_for_job", lambda db, job, *, nlp: [(db.users.get(candidate["id"]), score)])
    monkeypatch.setattr(recommendations, "upsert_recommendation", lambda db, candidate, job, *, nlp: SimpleNamespace(match_percentage=score))

    ranked = client.get(f"/api/v1/recommendations/jobs/{job['id']}/candidates", headers=owner)
    assert ranked.status_code == 200, ranked.text
    assert len(ranked.json()) == expected_count
    invitation = client.post(f"/api/v1/recommendations/jobs/{job['id']}/candidates/{candidate['id']}/invite", headers=owner)
    assert invitation.status_code == invite_status, invitation.text


def test_hiring_keeps_process_open_until_company_marks_job_filled(client):
    _, owner = company_account(client, "empresa-seleccion")
    first, first_headers = register(
        client,
        "candidato-uno",
        profession="Desarrollador Python",
        skills=["Python", "SQL", "FastAPI"],
        experience="Desarrollo de APIs con Python y SQL",
    )
    _, second_headers = register(
        client,
        "candidato-dos",
        profession="Desarrollador Python",
        skills=["Python", "SQL", "FastAPI"],
        experience="Desarrollo de APIs con Python y SQL",
    )
    job = create_job(client, owner)

    invite_url = (
        f"/api/v1/recommendations/jobs/{job['id']}/candidates/{first['id']}/invite"
    )
    invitation = client.post(invite_url, headers=owner)
    assert invitation.status_code == 200, invitation.text
    assert invitation.json()["type"] == "candidate_invitation"
    assert client.post(invite_url, headers=owner).json()["id"] == invitation.json()["id"]

    first_application = client.post(
        "/api/v1/applications", headers=first_headers, json={"job_id": job["id"]}
    ).json()
    second_application = client.post(
        "/api/v1/applications", headers=second_headers, json={"job_id": job["id"]}
    ).json()
    selected = client.put(
        f"/api/v1/applications/{first_application['id']}/status",
        headers=owner,
        json={"pipeline_stage": "hired"},
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["status"] == "hired"
    assert client.get(f"/api/v1/jobs/{job['id']}").json()["status"] == "active"

    still_active = client.get(
        "/api/v1/applications/me", headers=second_headers
    ).json()[0]
    assert still_active["id"] == second_application["id"]
    assert still_active["status"] != "rejected"
    notification_types_before_closing = {
        item["type"]
        for item in client.get(
            "/api/v1/notifications?unread_only=false", headers=second_headers
        ).json()
    }
    assert "application_not_selected" not in notification_types_before_closing

    covered = client.patch(
        f"/api/v1/jobs/{job['id']}", headers=owner, json={"status": "filled"}
    )
    assert covered.status_code == 200, covered.text
    assert covered.json()["status"] == "filled"

    finalized = client.get(
        "/api/v1/applications/me", headers=second_headers
    ).json()[0]
    assert finalized["id"] == second_application["id"]
    assert finalized["status"] == "rejected"
    assert finalized["resolution_reason"] == "another_candidate_selected"
    notification_types = {
        item["type"]
        for item in client.get(
            "/api/v1/notifications?unread_only=false", headers=second_headers
        ).json()
    }
    assert "application_not_selected" in notification_types


def test_rich_company_profile_following_and_compatible_job_alert(client):
    _, owner = company_account(client, "empresa-seguida")
    candidate, headers = register(
        client,
        "seguidor",
        profession="Desarrollador Python",
        skills=["Python", "SQL", "FastAPI"],
        experience="Desarrollo de APIs con Python y SQL",
    )
    company = client.get("/api/v1/companies/me", headers=owner).json()
    update = client.put(
        "/api/v1/companies/me",
        headers=owner,
        json={
            "description": "Creamos productos digitales para el sector financiero.",
            "website": "https://example.com",
            "sector": "Tecnología",
            "size": "51 a 200 personas",
            "location": "Bogotá",
            "mission": "Simplificar el acceso a servicios financieros.",
            "values": ["Transparencia", "Aprendizaje"],
            "benefits": ["Trabajo flexible", "Plan de formación"],
        },
    )
    assert update.status_code == 200, update.text
    public = client.get(f"/api/v1/companies/{company['id']}", headers=headers)
    assert public.status_code == 200
    assert public.json()["mission"].startswith("Simplificar")
    assert public.json()["values"] == ["Transparencia", "Aprendizaje"]

    follow_url = f"/api/v1/companies/{company['id']}/follow"
    followed = client.put(follow_url, headers=headers, json={"min_match": 60})
    assert followed.status_code == 200, followed.text
    assert followed.json() == {
        "company_id": company["id"],
        "is_following": True,
        "min_match": 60.0,
    }
    job = create_job(client, owner)
    alerts = client.get(
        "/api/v1/notifications?unread_only=false", headers=headers
    ).json()
    assert any(
        item["type"] == "company_job_match"
        and item["action_url"] == f"/vacantes/{job['id']}"
        for item in alerts
    )
    assert client.delete(follow_url, headers=headers).status_code == 204
    assert client.get(follow_url, headers=headers).json()["is_following"] is False


def test_company_logo_and_cover_are_saved_and_public(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    _, owner = company_account(client, "empresa-visual")
    _, candidate_headers = register(client, "visitante-empresa")
    company = client.get("/api/v1/companies/me", headers=owner).json()
    image = b"\x89PNG\r\n\x1a\n" + b"company-image"

    logo = client.post(
        "/api/v1/companies/me/logo",
        headers=owner,
        files={"file": ("logo.png", image, "image/png")},
    )
    assert logo.status_code == 200, logo.text
    assert logo.json()["logo_url"] == f"/api/v1/companies/{company['id']}/logo"
    cover = client.post(
        "/api/v1/companies/me/cover",
        headers=owner,
        files={"file": ("portada.png", image, "image/png")},
    )
    assert cover.status_code == 200, cover.text
    assert cover.json()["cover_url"] == f"/api/v1/companies/{company['id']}/cover"

    public = client.get(
        f"/api/v1/companies/{company['id']}", headers=candidate_headers
    ).json()
    assert public["logo_url"] == logo.json()["logo_url"]
    assert public["cover_url"] == cover.json()["cover_url"]
    assert client.get(public["logo_url"]).content == image
    assert client.get(public["cover_url"]).content == image


def test_profile_photo_and_resume_style_are_saved(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    user, headers = register(client, "perfil-visual")
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["resume_style"] = "modern"
    profile["resume_color"] = "teal"
    editable = {
        key: value
        for key, value in profile.items()
        if key
        not in {"id", "user_id", "cv_text", "cv_filename", "cv_uploaded_at", "photo_url"}
    }
    saved = client.put("/api/v1/profiles/me", headers=headers, json=editable)
    assert saved.status_code == 200, saved.text
    assert saved.json()["resume_style"] == "modern"
    assert saved.json()["resume_color"] == "teal"
    assert client.get("/api/v1/profiles/me", headers=headers).json()["resume_color"] == "teal"
    invalid = client.put("/api/v1/profiles/me", headers=headers, json={**editable, "resume_color": "not-a-palette"})
    assert invalid.status_code == 422

    image = b"\x89PNG\r\n\x1a\n" + b"local-profile-image"
    uploaded = client.post(
        "/api/v1/profiles/me/photo",
        headers=headers,
        files={"file": ("foto.png", image, "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["resume_color"] == "teal"
    assert uploaded.json()["photo_url"] == f"/api/v1/profiles/{user['id']}/photo"
    fetched = client.get(uploaded.json()["photo_url"])
    assert fetched.status_code == 200
    assert fetched.headers["content-type"].startswith("image/png")
    assert fetched.content == image

    _, company_headers = company_account(client, "foto-empresa")
    job = create_job(client, company_headers)
    assert client.get(f"/api/v1/profiles/candidates/{user['id']}", headers=company_headers).status_code == 403
    application = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]})
    assert application.status_code == 201, application.text
    visible = client.get(f"/api/v1/profiles/candidates/{user['id']}", headers=company_headers)
    assert visible.status_code == 200, visible.text
    assert visible.json()["photo_url"] == uploaded.json()["photo_url"]
    assert client.get(visible.json()["photo_url"]).content == image

    from app.api.deps import get_image_storage

    def failed_save(*args):
        from app.application.errors import UseCaseError
        raise UseCaseError(status_code=503, detail="No fue posible guardar la imagen")

    client.app.dependency_overrides[get_image_storage] = lambda: SimpleNamespace(save=failed_save)
    failed = client.post("/api/v1/profiles/me/photo", headers=headers, files={"file": ("nueva.png", image, "image/png")})
    assert failed.status_code == 503
    client.app.dependency_overrides.pop(get_image_storage)
    assert client.get("/api/v1/profiles/me", headers=headers).json()["photo_url"] == uploaded.json()["photo_url"]
    assert client.get(uploaded.json()["photo_url"]).content == image


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


def test_cv_is_persisted_in_blob_storage_when_configured(client, monkeypatch):
    uploaded = {}

    class FakeContainer:
        def upload_blob(self, **kwargs):
            uploaded.update(kwargs)

    monkeypatch.setattr(
        settings, "azure_storage_account_url", "https://example.blob.core.windows.net"
    )
    monkeypatch.setattr(
        resumes.ResumeReader, "_blob_container", lambda self: FakeContainer()
    )
    monkeypatch.setattr(resumes, "extract_pdf_text", lambda path: "Python y SQL")
    user, headers = register(client, "candidato-blob")

    response = client.post(
        "/api/v1/profiles/me/cv",
        headers=headers,
        files={"file": ("mi cv.pdf", b"%PDF-test", "application/pdf")},
    )

    assert response.status_code == 200, response.text
    assert uploaded["name"] == f"users/{user['id']}/cv.pdf"
    assert uploaded["data"] == b"%PDF-test"
    assert uploaded["overwrite"] is True
    assert uploaded["metadata"] == {"original_filename": "mi_cv.pdf"}
    assert uploaded["content_settings"].content_type == "application/pdf"


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
