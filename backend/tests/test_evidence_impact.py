# ruff: noqa: F811
from test_api_flows import client, company_account, create_job, register  # noqa: F401


def test_manual_evidence_changes_skills_only_when_explicitly_requested_and_recalculates_match(client):
    _, company = company_account(client)
    job = create_job(client, company)
    _, headers = register(client, "evidence-impact", skills=["Java"])
    endpoint = f"/api/v1/matching/jobs/{job['id']}"
    before = client.get(endpoint, headers=headers).json()
    payload = {"title": "Resultado de trabajo", "kind": "experience", "description": "Mejoré el proceso y documenté un resultado verificable.", "skills": ["Python", "SQL"]}
    saved = client.post("/api/v1/matching/evidence", headers=headers, json=payload)
    assert saved.status_code == 200 and not saved.json()[0]["verified"]
    assert client.get("/api/v1/profiles/me", headers=headers).json()["skills"] == ["java"]
    declared = client.get(endpoint, headers=headers).json()
    assert declared["overall_score"] == before["overall_score"]
    assert any(row["evidence"] for row in declared["requirements"])
    saved = client.post("/api/v1/matching/evidence", headers=headers, json={**payload, "add_to_profile": True}).json()
    after = client.get(endpoint, headers=headers).json()
    assert after["overall_score"] > before["overall_score"]
    assert all(row["covered"] for row in after["requirements"] if row["key"] in {"python", "sql"})
    assert all(not row["verified"] for row in saved)
    assert client.delete(f"/api/v1/matching/evidence/{saved[-1]['id']}", headers=headers).status_code == 204
    assert set(client.get("/api/v1/profiles/me", headers=headers).json()["skills"]) == {"java", "python", "sql"}


def test_company_cannot_use_candidate_privacy_learning_or_evidence(client):
    _, headers = company_account(client)
    for path in ["/account/privacy", "/learning/catalog", "/matching/evidence", "/matching/preferences", "/personalization/feedback"]:
        assert client.get("/api/v1" + path, headers=headers).status_code == 403
