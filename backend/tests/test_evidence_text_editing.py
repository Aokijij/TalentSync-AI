# ruff: noqa: F811
from copy import deepcopy

import pytest
from test_api_flows import client, company_account, register  # noqa: F401

from app.infrastructure.database.models import EventLog, User


def save_evidence(client, headers, **changes):
    response = client.post("/api/v1/matching/evidence", headers=headers, json={
        "title": "Proyecto original", "kind": "repository", "url": "https://github.com/example/project",
        "description": "Participé en el desarrollo del proyecto.", "skills": ["python"], **changes,
    })
    assert response.status_code == 200
    return response.json()[-1]


def test_owner_can_correct_text_without_losing_reference_analysis_or_other_evidence(client):
    owner, headers = register(client, "evidence-text-owner", skills=["Java"])
    first = save_evidence(client, headers, add_to_profile=True)
    second = save_evidence(client, headers, title="Otro proyecto")
    with client.session_factory() as db:
        profile = db.get(User, owner["id"]).profile
        profile.evidence = [{**row, "analysis": {"origin": "github_public", "revision": "original-revision", "skills": ["python"]},
                             "source": "github_public", "custom_metadata": "preserve"}
                            if row["id"] == first["id"] else row for row in profile.evidence]
        db.commit()
        original = deepcopy(profile.evidence[0])
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    text = {"title": "TalentSync AI", "description": "Desarrollé la plataforma y diseñé su interfaz para candidatos y empresas."}
    response = client.patch(f"/api/v1/matching/evidence/{first['id']}", headers=headers,
                            json={key: f"  {value}  " for key, value in text.items()})
    assert response.status_code == 200
    assert response.json() == [{**original, **text}, second]
    assert client.get("/api/v1/matching/evidence", headers=headers).json() == response.json()
    after = client.get("/api/v1/profiles/me", headers=headers).json()
    for key in ("skills", "skill_levels", "certifications", "experience", "summary_mode"):
        assert after[key] == before[key]
    with client.session_factory() as db:
        event = db.query(EventLog).filter_by(event_type="profile.evidence_edited").one()
        assert event.actor_user_id == owner["id"] and event.details == {}


def test_evidence_text_editing_is_owner_only_and_requires_candidate_role(client):
    _, headers = register(client, "evidence-edit-owner")
    row = save_evidence(client, headers)
    _, other = register(client, "evidence-edit-other")
    _, company = company_account(client)
    path = f"/api/v1/matching/evidence/{row['id']}"
    text = {"title": "Título corregido", "description": "Descripción corregida de mi aporte."}
    assert client.patch(path, headers=other, json=text).status_code == 404
    assert client.patch(path, headers=company, json=text).status_code == 403
    assert client.patch(path, json=text).status_code == 401
    assert client.patch("/api/v1/matching/evidence/missing", headers=headers, json=text).status_code == 404
    assert client.get("/api/v1/matching/evidence", headers=headers).json() == [row]
    with client.session_factory() as db:
        assert db.query(EventLog).filter_by(event_type="profile.evidence_edited").count() == 0


@pytest.mark.parametrize("changes", [
    {"title": "  "}, {"description": "   "}, {"title": "a" * 161}, {"description": "a" * 2001},
    {"verified": True}, {"analysis": {"revision": "forged"}}, {"skills": ["sql"]},
    {"url": "https://example.com/changed"}, {"add_to_profile": True}, {"kind": "certificate"},
])
def test_text_edit_rejects_invalid_text_or_changes_to_reference_metadata(client, changes):
    _, headers = register(client, "invalid-evidence-edit")
    row = save_evidence(client, headers)
    response = client.patch(f"/api/v1/matching/evidence/{row['id']}", headers=headers, json={
        "title": "Título corregido", "description": "Descripción corregida de mi aporte.", **changes,
    })
    assert response.status_code == 422
    assert client.get("/api/v1/matching/evidence", headers=headers).json() == [row]


@pytest.mark.parametrize("added_to_profile", [False, True])
def test_certificate_text_stays_in_sync_without_adding_unpublished_certificates(client, added_to_profile):
    _, headers = register(client, "certificate-text-edit")
    row = save_evidence(client, headers, kind="certificate", issuer="Entidad original", year="2025", add_to_profile=added_to_profile)
    text = {"title": "Certificado corregido", "description": "Completé la formación y desarrollé ejercicios prácticos."}
    path = f"/api/v1/matching/evidence/{row['id']}"
    assert client.patch(path, headers=headers, json=text).status_code == 200
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    assert len(profile["certifications"]) == int(added_to_profile)
    if added_to_profile:
        certificate = profile["certifications"][0]
        assert certificate["name"] == text["title"] and certificate["description"] == text["description"]
        assert certificate["evidence_id"] == row["id"]
        assert certificate["issuer"] == row["issuer"] and certificate["year"] == row["year"]
        assert certificate["url"] == row["url"]
