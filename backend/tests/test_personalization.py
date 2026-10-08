# ruff: noqa: F811
from types import SimpleNamespace

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.entities.enums import UserRole
from app.domain.services.personalization import (
    collaborative_interest,
    synthetic_email,
    training_gate,
)
from app.infrastructure.database.models import (
    Company,
    CompanyMember,
    RecommendationFeedback,
    User,
)
from app.infrastructure.nlp.interest_trainer import InterestTrainer
from app.infrastructure.nlp.matching_encoder import LocalMatchingEncoder


def privacy(client, headers, enabled):
    return client.put("/api/v1/account/privacy", headers=headers, json={"share_evidence": True, "notify_new_skills": False, "personalize_recommendations": enabled})


def test_feedback_requires_consent_hides_without_changing_affinity_and_withdraws(client):
    _, company = company_account(client)
    job = create_job(client, company)
    _, candidate = register(client, "preference-candidate", skills=["python", "sql"])
    endpoint = "/api/v1/personalization/feedback"
    payload = {"job_id": job["id"], "interested": False}
    baseline = client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=candidate).json()[0]["match_percentage"]
    assert client.put(endpoint, headers=candidate, json=payload).status_code == 403
    assert privacy(client, candidate, True).status_code == 200
    assert client.put(endpoint, headers=candidate, json=payload).status_code == 200
    assert client.put(endpoint, headers=candidate, json=payload).status_code == 200
    assert len(client.get(endpoint, headers=candidate).json()) == 1
    assert client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=candidate).json() == []
    assert client.put(endpoint, headers=candidate, json={**payload, "interested": True}).status_code == 200
    recommended = client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=candidate).json()[0]
    assert recommended["match_percentage"] == baseline
    assert recommended["personalization"]["enabled"] is True
    assert privacy(client, candidate, False).status_code == 200
    assert client.get(endpoint, headers=candidate).json() == []
    assert client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=candidate).json()[0]["personalization"] == {"enabled": False}


def test_training_excludes_reserved_test_domains_and_waits_for_real_data(client):
    _, company = company_account(client)
    job = create_job(client, company)
    user, headers = register(client, "model-admin", skills=["python", "sql"])
    privacy(client, headers, True)
    assert client.put("/api/v1/personalization/feedback", headers=headers, json={"job_id": job["id"], "interested": True}).status_code == 200
    with client.session_factory() as db:
        db.get(User, user["id"]).role = UserRole.ADMIN
        db.commit()
    status = client.get("/api/v1/admin/models", headers=headers).json()
    assert status["training_data"]["rows"] == 0
    assert status["text_method"] == "lexical-hashing-v1"
    result = client.post("/api/v1/admin/models/train", headers=headers)
    assert result.status_code == 200
    assert result.json()["status"] == "insufficient_data"
    assert client.get("/api/v1/admin/models", headers=headers).json()["experiments"][0]["status"] == "insufficient_data"


def test_collaborative_signal_requires_three_distinct_consented_neighbors():
    profile = SimpleNamespace(user_id=1, skills=["python", "sql"])
    def signal(user_id, interested, enabled=True):
        return SimpleNamespace(user_id=user_id, job_id=10, interested=interested,
            user=SimpleNamespace(role="candidate", privacy_preferences={"personalize_recommendations": enabled}, profile=SimpleNamespace(skills=["python", "sql"])))
    assert collaborative_interest(profile, 10, [signal(2, True), signal(2, True), signal(3, True), signal(4, True, False)])["score"] is None
    result = collaborative_interest(profile, 10, [signal(2, True), signal(3, True), signal(4, False)])
    assert result["score"] == 66.7
    assert "user_ids" not in result


def test_offline_training_holds_out_users_and_records_artifact():
    rows = [{"user_id": user, "job_id": job, "label": job % 2, "features": [90 if job % 2 else 10, 50, 50, 50, 0, 50]}
            for user in range(20) for job in range(10)]
    assert training_gate(rows)["ready"] is True
    assert training_gate(rows[:99])["ready"] is False
    result = InterestTrainer().fit(rows)
    assert result["status"] == "validated_shadow"
    assert result["metrics"]["auc"] == 1
    assert result["metrics"]["active_in_ranking"] is False
    assert result["metrics"]["split"] == "held_out_users_seed_42"
    assert len(result["artifact"]["coefficients"]) == 6
    assert synthetic_email("candidate@talentsync.example.com")
    assert synthetic_email("person@example.org")
    assert not synthetic_email("person@business.co")


def test_optional_encoder_refuses_remote_names_and_executable_weights(tmp_path):
    with pytest.raises(ValueError, match="carpeta absoluta"):
        LocalMatchingEncoder("remote/model-name")
    (tmp_path / "pytorch_model.bin").write_bytes(b"not-loaded")
    with pytest.raises(ValueError, match="safetensors"):
        LocalMatchingEncoder(str(tmp_path))


def test_admin_deletes_member_without_deleting_organization_and_cleans_candidate_signals(client):
    _, company = company_account(client)
    job = create_job(client, company)
    member, _ = register(client, "deletable-member")
    admin, headers = register(client, "deletion-admin")
    candidate, candidate_headers = register(client, "deletable-candidate", skills=["python"])
    privacy(client, candidate_headers, True)
    client.put("/api/v1/personalization/feedback", headers=candidate_headers, json={"job_id": job["id"], "interested": True})
    with client.session_factory() as db:
        db.get(User, admin["id"]).role = UserRole.ADMIN
        db.get(User, member["id"]).role = UserRole.COMPANY
        db.add(CompanyMember(user_id=member["id"], company_id=job["company_id"], role="interviewer", active=True, assigned_job_ids=[]))
        db.commit()
    assert client.delete(f"/api/v1/admin/users/{member['id']}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/admin/users/{candidate['id']}", headers=headers).status_code == 204
    with client.session_factory() as db:
        assert db.get(Company, job["company_id"]) is not None
        assert db.query(CompanyMember).filter_by(user_id=member["id"]).count() == 0
        assert db.query(RecommendationFeedback).filter_by(user_id=candidate["id"]).count() == 0
