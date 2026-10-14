# ruff: noqa: F811
from test_api_flows import client  # noqa: F401
from test_career_coach_workspace import BASE, candidate, proposal

from app.infrastructure.database.models import User


def test_applied_context_is_private_and_manual_proposal_edits_replace_it(client):
    user, headers = candidate(client, "context-action-person")
    item = proposal(client, headers)
    client.put(BASE + f"/writing/{item['id']}", headers=headers, json={"action": "apply"}).raise_for_status()
    with client.session_factory() as db:
        context = db.get(User, user["id"]).profile.preferences["writing_contexts"]
        assert context[0]["record"]["description"] == item["before"]
    assert "writing_contexts" not in client.get("/api/v1/profiles/me", headers=headers).json()
    client.put(BASE + f"/writing/{item['id']}", headers=headers, json={"action": "undo"}).raise_for_status()
    item = proposal(client, headers)
    client.put(BASE + f"/writing/{item['id']}", headers=headers, json={"action": "apply", "text": "Texto corregido personalmente"}).raise_for_status()
    with client.session_factory() as db:
        assert db.get(User, user["id"]).profile.preferences["writing_contexts"] == []
