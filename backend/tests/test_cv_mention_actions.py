# ruff: noqa: F811
from test_api_flows import client, company_account, register  # noqa: F401

from app.infrastructure.database.models import User


def test_candidate_can_confirm_dismiss_and_restore_only_own_mentions(client):
    user, headers = register(client, "mention-owner", skills=[])
    _, other = register(client, "mention-other", skills=[])
    with client.session_factory() as db:
        profile = db.get(User, user["id"]).profile
        profile.preferences = {"cv_context_version": "skill-context-v2", "cv_skill_context": [{"skill": "css", "state": "unknown", "excerpt": "CSS3", "reason": "Contexto por confirmar"}, {"skill": "python", "state": "learning", "excerpt": "Aprendiendo Python"}]}
        db.commit()
    endpoint = "/api/v1/profiles/me/cv-mentions"
    confirmed = client.patch(endpoint, headers=headers, json={"skill": "css", "action": "confirm"})
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["skills"] == ["css"] and confirmed.json()["cv_mention_decisions"]["css"] == "confirmed"
    again = client.patch(endpoint, headers=headers, json={"skill": "css", "action": "confirm"})
    assert again.json()["skills"] == ["css"]
    dismissed = client.patch(endpoint, headers=headers, json={"skill": "python", "action": "dismiss"})
    assert dismissed.json()["skills"] == ["css"] and dismissed.json()["cv_mention_decisions"]["python"] == "dismissed"
    assert any(row["skill"] == "python" for row in dismissed.json()["cv_skill_context"])
    restored = client.patch(endpoint, headers=headers, json={"skill": "python", "action": "restore"})
    assert "python" not in restored.json()["cv_mention_decisions"] and restored.json()["skills"] == ["css"]
    assert client.patch(endpoint, headers=other, json={"skill": "css", "action": "confirm"}).status_code == 404
    assert client.patch(endpoint, headers=headers, json={"skill": "inventada", "action": "confirm"}).status_code == 404
    _, company = company_account(client, "mentions-company")
    assert client.patch(endpoint, headers=company, json={"skill": "css", "action": "confirm"}).status_code == 403
    assert client.patch(endpoint, json={"skill": "css", "action": "confirm"}).status_code == 401
