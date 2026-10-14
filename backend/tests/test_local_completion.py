# ruff: noqa: F811
from datetime import datetime, timedelta
from types import SimpleNamespace

from test_api_flows import client, company_account, register  # noqa: F401
from test_ecosystem import administrator
from test_offer_quality import complete_offer

from app.domain.entities.enums import UserRole
from app.domain.services.discovery import discovery_key, discovery_signals
from app.domain.services.offer_writing import writing_draft
from app.domain.services.reputation import company_health
from app.infrastructure.database.models import (
    Company,
    CompanyInvitation,
    CompanyMember,
    Job,
    TrustIncident,
    User,
)


def test_full_verification_and_company_directories_beyond_200(client):
    account, owner = company_account(client, "directory-owner")
    candidate, candidate_headers = register(client, "directory-reporter")
    with client.session_factory() as db:
        companies = [Company(owner_user_id=account["id"], name=f"Directorio {i:03}", nit=f"DIR-{i}", is_external=False,
                             verification_required=True, verification_status="reviewing") for i in range(205)]
        db.add_all(companies)
        db.flush()
        last = companies[-1].id
        companies[-1].verification_status = "suspended"
        for state in ["confirmed", "appealed"]:
            db.add(TrustIncident(company_id=last, reporter_user_id=candidate["id"], category="other", status=state, details="Hechos reservados de esta prueba.", appeal={}))
        db.commit()
        health = company_health(companies[-1])
    admin = administrator(client)
    endpoint = "/api/v1/admin/verification-queue"
    result = client.get(endpoint, headers=admin).json()
    assert result["total"] >= 205 and len(result["items"]) == 5
    tail = client.get(endpoint, headers=admin, params={"page": 999}).json()
    assert tail["page"] > 40 and tail["items"]
    found = client.get(endpoint, headers=admin, params={"search": "DIR-204", "status": "suspended"}).json()
    assert found["total"] == 1 and found["items"][0]["id"] == last
    assert client.get(endpoint, headers=admin, params={"search": "%"}).json()["total"] == 0
    assert client.get(endpoint, headers=owner).status_code == 403
    assert client.get(endpoint, headers=candidate_headers).status_code == 403
    endpoint = "/api/v1/admin/company-directory"
    result = client.get(endpoint, headers=admin).json()
    assert result["total"] >= 205 and len(result["items"]) == 6
    assert result["items"][0]["id"] == last
    assert {key: result["items"][0][key] for key in health} == health
    found = client.get(endpoint, headers=admin, params={"search": "Directorio 204", "filter": "attention"}).json()
    assert found["total"] == 1 and "details" not in str(found)
    assert client.get(endpoint, headers=admin, params={"search": "Directorio", "filter": "rated"}).json()["total"] == 1
    assert client.get(endpoint, headers=admin, params={"search": "Directorio", "filter": "unrated"}).json()["total"] == 204
    assert client.get(endpoint, headers=admin, params={"page": 999}).json()["page"] > 34
    assert client.get(endpoint, headers=owner).status_code == 403
    assert client.get(endpoint, headers=admin, params={"page_size": 51}).status_code == 422
    assert client.get("/api/v1/admin/ecosystem?include_companies=false", headers=admin).json()["companies"] == []


def test_team_page_is_complete_scoped_and_does_not_expose_invitation_tokens(client):
    account, owner = company_account(client, "team-page-owner")
    with client.session_factory() as db:
        company = db.query(Company).filter_by(owner_user_id=account["id"]).first()
        original = db.get(User, account["id"])
        for index in range(205):
            user = User(name=f"Integrante {index:03}", email=f"team-{index}@example.test", password_hash=original.password_hash, role=UserRole.COMPANY)
            db.add(user)
            db.flush()
            db.add(CompanyMember(company_id=company.id, user_id=user.id, role="interviewer", active=index != 204, assigned_job_ids=[]))
            db.add(CompanyInvitation(company_id=company.id, email=f"invite-{index}@example.test", role="recruiter", assigned_job_ids=[], token_hash=f"PRIVATE-TOKEN-{index}", expires_at=datetime.utcnow() + timedelta(days=1)))
        db.commit()
    endpoint = "/api/v1/organization/team-page"
    result = client.get(endpoint, headers=owner).json()
    assert result["total"] == 205 and len(result["items"]) == 6
    assert result["counts"]["active"] == 204 and result["counts"]["revoked"] == 1
    found = client.get(endpoint, headers=owner, params={"search": "Integrante 204", "status": "revoked"}).json()
    assert found["total"] == 1 and found["items"][0]["active"] is False
    assert client.get(endpoint, headers=owner, params={"search": "entrevistador"}).json()["total"] == 205
    invitations = client.get(endpoint, headers=owner, params={"kind": "invitations", "page": 35})
    assert invitations.json()["total"] == 205 and len(invitations.json()["items"]) == 1
    assert "PRIVATE-TOKEN" not in invitations.text and "token_hash" not in invitations.text
    target = client.get(endpoint, headers=owner, params={"kind": "invitations", "search": "invite-204@"}).json()["items"][0]
    assert client.delete(f"/api/v1/organization/invitations/{target['id']}", headers=owner).status_code == 200
    assert client.get(endpoint, headers=owner, params={"kind": "invitations", "status": "expired"}).json()["total"] == 1
    assert client.get(endpoint, headers=owner, params={"status": "accepted"}).status_code == 422
    _, other = company_account(client, "team-page-other")
    assert client.get(endpoint, headers=other).json()["total"] == 0
    _, candidate = register(client, "team-page-candidate")
    assert client.get(endpoint, headers=candidate).status_code == 403


def test_writing_uses_supplied_facts_and_never_saves_or_crosses_company_access(client):
    _, owner = company_account(client, "writing-owner")
    payload = {**complete_offer(), "status": "draft"}
    job = client.post("/api/v1/jobs", headers=owner, json=payload).json()
    result = client.post("/api/v1/hiring/quality/writing", headers=owner, json={**payload, "job_id": job["id"]})
    assert result.status_code == 200, result.text
    proposals = {row["field"]: row for row in result.json()["proposals"]}
    assert "60 días" in proposals["description"]["text"]
    assert "SQL".lower() in proposals["requirements"]["text"].lower()
    assert "No se exige experiencia laboral previa" in proposals["requirements"]["text"]
    assert "No se exige" not in proposals["description"]["text"]
    with client.session_factory() as db:
        assert db.get(Job, job["id"]).description == payload["description"]
        assert db.get(Job, job["id"]).status == "draft"
    _, other = company_account(client, "writing-outsider")
    assert client.post("/api/v1/hiring/quality/writing", headers=other, json={**payload, "job_id": job["id"]}).status_code == 403
    _, candidate = register(client, "writing-reader")
    assert client.post("/api/v1/hiring/quality/writing", headers=candidate, json=payload).status_code == 403
    blank = writing_draft(SimpleNamespace(title="", description="", requirements="", quality_details={}, skill_requirements=[]))
    assert blank["proposals"] == [] and len(blank["questions"]) == 3


def test_discovery_clarity_can_advance_nearby_affinity_without_overriding_trust():
    def row(identifier, match, quality, *, reduced=False):
        return SimpleNamespace(job_id=identifier, match_percentage=match, personalization={"enabled": False},
                               discovery={"quality_bonus": (quality - 50) * .25, "affinity_band": min(9, int(match // 10)), "visibility_reduced": reduced})
    low_quality, clear = row(1, 77, 10), row(2, 74, 100)
    stronger, reduced = row(3, 80, 10), row(4, 99, 100, reduced=True)
    assert [item.job_id for item in sorted([low_quality, clear, stronger, reduced], key=discovery_key)] == [2, 3, 1, 4]
    assert low_quality.match_percentage == 77 and clear.match_percentage == 74
    external = discovery_signals(SimpleNamespace(source_kind="external"), 74)
    assert external["quality_score"] is None and external["quality_bonus"] == 0


def test_recommendation_api_explains_quality_without_changing_match(client):
    _, owner = company_account(client, "discovery-api")
    complete = complete_offer()
    high = client.post("/api/v1/jobs", headers=owner, json=complete).json()
    legacy = {key: value for key, value in complete.items() if key != "quality_details"}
    low = client.post("/api/v1/jobs", headers=owner, json=legacy).json()
    _, candidate = register(client, "discovery-candidate", profession="Analista de datos", skills=["sql"])
    result = client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=candidate)
    assert result.status_code == 200, result.text
    rows = {row["job_id"]: row for row in result.json()}
    assert rows[high["id"]]["match_percentage"] == rows[low["id"]]["match_percentage"]
    assert rows[high["id"]]["discovery"]["quality_score"] == 100
    assert rows[high["id"]]["discovery"]["quality_score"] > rows[low["id"]]["discovery"]["quality_score"]
    assert result.json()[0]["job_id"] == high["id"]
    cached = client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=candidate).json()
    assert [row["job_id"] for row in cached] == [row["job_id"] for row in result.json()]


def test_integration_readiness_distinguishes_local_and_configured_without_secrets():
    from app.domain.services.integration_readiness import integration_readiness
    rows = integration_readiness(neural_active=True, local_mail=True, smtp=False, providers={"google": True}, catalog=False)
    assert all(set(row) <= {"name", "state", "status", "next_steps", "action_url", "action_label"} for row in rows)
    states = {row["name"]: row["state"] for row in rows}
    assert states["Acceso social"] == "configured"
    assert states["SSO administrativo"] == "provider_required"
    assert states["Correo y avisos"] == "local_ready"
    assert states["Verificación empresarial"] == "local_manual"
