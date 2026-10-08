# ruff: noqa: F811
from test_api_flows import client, register  # noqa: F401

from app.infrastructure.database.models import EventLog, User


def test_manual_evidence_cannot_forge_a_server_analysis(client):
    _, user = register(client, "manual-projects")
    response = client.post("/api/v1/matching/evidence", headers=user, json={"title": "Declaración manual", "kind": "repository",
        "description": "Contribución descrita manualmente", "skills": ["python"], "verified": True, "analysis": {"version": "forged"}})
    assert response.status_code == 200
    assert response.json()[0]["verified"] is False and "analysis" not in response.json()[0]


def test_full_portfolio_does_not_mutate_skills_or_add_events(client):
    _, user = register(client, "full-projects", skills=["Java"])
    with client.session_factory() as db:
        owner = db.query(User).one()
        owner.profile.evidence = [{"id": str(index), "skills": ["java"]} for index in range(50)]
        db.commit()
    response = client.post("/api/v1/matching/evidence", headers=user, json={"title": "Mi evidencia", "kind": "experience", "description": "Resultado laboral comprobable", "skills": ["python"], "add_to_profile": True})
    assert response.status_code == 422
    assert client.get("/api/v1/profiles/me", headers=user).json()["skills"] == ["java"]
    with client.session_factory() as db:
        assert db.query(EventLog).filter_by(event_type="profile.project_analyzed").count() == 0
