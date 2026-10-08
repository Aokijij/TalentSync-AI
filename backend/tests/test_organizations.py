import re
from urllib.parse import parse_qs, urlparse

from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import Company, User
from app.infrastructure.security.jwt import create_access_token


def verified_email(client, user):
    with client.session_factory() as db:
        db.get(User, user["id"]).email_verified = True
        db.commit()


def admin_account(client):
    user, _ = register(client, "admin-review")
    with client.session_factory() as db:
        db.get(User, user["id"]).role = UserRole.ADMIN
        db.commit()
    return {"Authorization": f"Bearer {create_access_token(str(user['id']), 'admin')}"}


def test_drafts_require_review_before_publication(client):
    user, headers = company_account(client)
    verified_email(client, user)
    with client.session_factory() as db:
        db.query(Company).one().verification_required = True
        db.commit()
    job = create_job(client, headers)
    assert job["status"] == "draft"
    assert client.get("/api/v1/jobs", params={"status": ""}).json() == []
    assert client.get(f"/api/v1/jobs/{job['id']}").status_code == 404
    _, candidate = register(client, "candidate-draft")
    assert client.get(f"/api/v1/jobs/{job['id']}", headers=candidate).status_code == 403
    assert client.post(f"/api/v1/jobs/{job['id']}/match", headers=candidate).status_code == 404
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=headers, json={"status": "active"}).status_code == 403
    assert client.get("/api/v1/organization/assignments", headers=headers).status_code == 403
    assert client.post("/api/v1/organization/verification", headers=headers, json={"legal_name": "Empresa laboratorio", "registry_reference": "Registro local 1234", "representative_role": "Director"}).status_code == 200
    admin = admin_account(client)
    queue = client.get("/api/v1/admin/verifications", headers=admin).json()
    assert queue[0]["status"] == "reviewing"
    assert client.post(f"/api/v1/admin/verifications/{job['company_id']}", headers=admin, json={"status": "verified", "feedback": "Documentación local revisada"}).status_code == 200
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=headers, json={"status": "active"}).status_code == 200
    assert len(client.get("/api/v1/jobs").json()) == 1
    assert client.post(f"/api/v1/admin/verifications/{job['company_id']}", headers=admin, json={"status": "suspended", "feedback": "Suspensión de prueba documentada"}).status_code == 200
    assert client.get("/api/v1/jobs").json() == []
    assert client.patch(f"/api/v1/jobs/{job['id']}", headers=headers, json={"status": "active"}).status_code == 403


def test_invitation_binding_one_use_roles_and_removed_access(client, monkeypatch):
    monkeypatch.setattr(settings, "local_mail_enabled", True)
    monkeypatch.setattr(settings, "database_url", "sqlite://")
    owner, headers = company_account(client)
    verified_email(client, owner)
    job = create_job(client, headers)
    _, other_headers = company_account(client, "other-company")
    other_job = create_job(client, other_headers)
    endpoint = "/api/v1/organization/invitations"
    assert client.post(endpoint, headers=headers, json={"email": "member@example.com", "role": "interviewer", "assigned_job_ids": [other_job["id"]]}).status_code == 422
    assert client.post(endpoint, headers=headers, json={"email": "member@example.com", "role": "interviewer", "assigned_job_ids": [job["id"]]}).status_code == 200
    mail = client.get("/api/v1/dev/mailbox").json()[0]
    token = parse_qs(urlparse(re.search(r"https?://\S+", mail["body"]).group()).query)["token"][0]
    wrong = client.post("/api/v1/auth/register", json={"name": "Wrong user", "email": "wrong@example.com", "password": "Test-password-2026!", "role": "company", "invitation_token": token})
    assert wrong.status_code == 422
    member, member_headers = register(client, "member", "company", invitation_token=token)
    assert client.post(endpoint + "/accept", headers=member_headers, json={"token": token}).status_code == 403
    verified_email(client, member)
    assert client.post(endpoint + "/accept", headers=member_headers, json={"token": token}).status_code == 200
    assert client.post(endpoint + "/accept", headers=member_headers, json={"token": token}).status_code == 404
    assignments = client.get("/api/v1/organization/assignments", headers=member_headers).json()
    assert [row["job_id"] for row in assignments] == [job["id"]]
    assert client.get("/api/v1/jobs", headers=member_headers).status_code == 403
    assert client.get("/api/v1/organization/team", headers=member_headers).status_code == 403
    membership = client.get("/api/v1/organization/team", headers=headers).json()[0]
    update = f"/api/v1/organization/team/{membership['id']}"
    assert client.patch(update, headers=headers, json={"role": "recruiter", "active": True, "assigned_job_ids": []}).status_code == 200
    assert client.put("/api/v1/companies/me", headers=member_headers, json={"name": "Hijacked"}).status_code == 403
    assert client.patch(f"/api/v1/jobs/{other_job['id']}", headers=member_headers, json={"title": "Hijacked"}).status_code == 403
    assert client.patch(update, headers=headers, json={"role": "recruiter", "active": False, "assigned_job_ids": []}).status_code == 200
    assert client.get("/api/v1/organization/me", headers=member_headers).status_code in {403, 404}
