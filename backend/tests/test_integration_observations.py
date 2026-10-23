# ruff: noqa: F811
import json
from datetime import datetime, timedelta

import pytest
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator

from app.api.deps import get_youtube_learning
from app.application.errors import UseCaseError
from app.application.use_cases.integration_observations import observations, observed
from app.core.config import settings
from app.domain.services.integration_readiness import integration_readiness
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_readiness_separates_configuration_observation_errors_and_old_results():
    now = datetime(2026, 10, 22, 15)
    rows = integration_readiness(neural_active=False, local_mail=True, smtp=False, resend=True, providers={}, catalog=False, youtube=True, learn=True,
        observations={"youtube": {"last_success_at": now.isoformat() + "Z", "last_attempt_at": now.isoformat() + "Z", "last_error": ""},
                      "microsoft_learn": {"last_success_at": (now - timedelta(days=2)).isoformat() + "Z", "last_attempt_at": (now - timedelta(days=2)).isoformat() + "Z", "last_error": ""}}, now=now)
    indexed = {row["id"]: row for row in rows}
    assert indexed["youtube"]["configured"] and indexed["youtube"]["operational_state"] == "observed"
    assert indexed["microsoft_learn"]["operational_state"] == "stale"
    assert indexed["mail"]["operational_state"] == "local"  # Local transport wins over stale external flags.
    assert indexed["social"]["operational_state"] == "not_configured"
    assert "20 empresas" in indexed["salary"]["status"] and "todo el país" in indexed["salary"]["status"]
    assert "codewars" not in indexed and "github_projects" not in indexed


def test_observation_preserves_last_success_sanitizes_errors_and_ignores_input_errors(client):
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        assert observed(db, "youtube", lambda: {"items": []}) == {"items": []}
        previous = observations(db)["youtube"]["last_success_at"]
        def fail():
            raise UseCaseError(status_code=503, detail="PRIVATE-KEY provider-url?token=SECRET")
        with pytest.raises(UseCaseError):
            observed(db, "youtube", fail)
        result = observations(db)
        assert result["youtube"]["last_success_at"] == previous
        assert result["youtube"]["last_error"]
        assert "PRIVATE" not in json.dumps(result) and "SECRET" not in json.dumps(result)
        def invalid():
            raise UseCaseError(status_code=422, detail="Bad input")
        with pytest.raises(UseCaseError):
            observed(db, "sena", invalid)
        assert "sena" not in observations(db)
        observed(db, "youtube", lambda: {"items": []})
        assert observations(db)["youtube"]["last_error"] == ""


def test_partial_and_quota_results_do_not_erase_a_success(client):
    with client.session_factory() as session:
        db = SqlAlchemyUnitOfWork(session)
        observed(db, "sena", lambda: {"checked": 3, "failed": 0})
        success = observations(db)["sena"]["last_success_at"]
        observed(db, "sena", lambda: {"checked": 1, "failed": 2})
        assert observations(db)["sena"]["last_success_at"] == success
        assert "parcial" in observations(db)["sena"]["last_error"]
        def quota():
            raise UseCaseError(status_code=429, detail="PRIVATE")
        with pytest.raises(UseCaseError):
            observed(db, "sena", quota)
        assert "cuota" in observations(db)["sena"]["last_error"]


def test_admin_panel_is_read_only_and_preview_observations_persist_without_secrets(client, monkeypatch):
    monkeypatch.setattr(settings, "youtube_learning_enabled", True)
    monkeypatch.setattr(settings, "youtube_api_key", "fixture-only-key")
    class Gateway:
        def preview(self, url, actor_id):
            if "failure" in url:
                raise UseCaseError(status_code=503, detail="PRIVATE provider failure")
            return {"preview_id": "x" * 24, "items": []}
    client.app.dependency_overrides[get_youtube_learning] = Gateway
    admin = administrator(client)
    _, candidate = register(client, "readiness-viewer")
    root = "/api/v1/admin/models"
    assert client.get(root, headers=candidate).status_code == 403
    before = client.get(root, headers=admin)
    assert before.status_code == 200
    assert client.post("/api/v1/admin/learning/sources/youtube/preview", headers=admin, json={"url": "https://www.youtube.com/playlist?list=fixture"}).status_code == 200
    with client.session_factory() as session:
        seen = observations(SqlAlchemyUnitOfWork(session))["youtube"]
        assert seen["last_success_at"]
    assert client.post("/api/v1/admin/learning/sources/youtube/preview", headers=admin, json={"url": "https://www.youtube.com/playlist?list=failure"}).status_code == 503
    response = client.get(root, headers=admin)
    row = next(row for row in response.json()["integrations"] if row["id"] == "youtube")
    assert row["last_attempt_at"] and row["last_success_at"]
    assert row["operational_state"] == "error" and row["last_error"]
    assert "PRIVATE" not in response.text
    # GET only reads persisted evidence; never calls the preview method.
    assert client.get(root, headers=admin).json()["integrations"] == response.json()["integrations"]
