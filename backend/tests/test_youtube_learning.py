# ruff: noqa: F811
from types import SimpleNamespace

import httpx
import pytest
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator

from app.api.deps import get_youtube_learning
from app.application.errors import UseCaseError
from app.infrastructure.database import session as database_session
from app.infrastructure.database.models import EventLog, LearningResource
from app.infrastructure.youtube_learning import YouTubeLearning, playlist_id

IDENTIFIER = "PLtest_playlist_12345"
PREFIX = "/api/v1/admin/learning/sources/youtube"


def make_gateway(*, enabled=True, limit=100, response=None):
    calls = []
    def handle(request):
        calls.append(request)
        if response:
            return response(request)
        if request.url.path.endswith("/playlists"):
            return httpx.Response(200, json={"items": [{"id": IDENTIFIER, "snippet": {
                "title": "API original title", "channelTitle": "API creator", "description": "API original description"},
                "status": {"privacyStatus": "public"}, "contentDetails": {"itemCount": 25}}]})
        return httpx.Response(200, json={"items": [
            {"snippet": {"title": "API sample title", "resourceId": {"videoId": "12345678901"}}},
            {"snippet": {"title": "Private video", "resourceId": {"videoId": "12345678902"}}},
            {"snippet": {"title": "Malicious URL", "resourceId": {"videoId": "../private"}}},
        ]})
    settings = SimpleNamespace(youtube_learning_enabled=enabled, youtube_api_key="unit-test-private-key",
                               youtube_learning_daily_requests=limit)
    return YouTubeLearning(settings, httpx.MockTransport(handle)), calls


@pytest.mark.parametrize("value", [IDENTIFIER, f"https://www.youtube.com/playlist?list={IDENTIFIER}",
                                    f"https://m.youtube.com/watch?v=12345678901&list={IDENTIFIER}"])
def test_playlist_reference_normalizes_without_fetching_the_supplied_url(value):
    assert playlist_id(value) == IDENTIFIER


@pytest.mark.parametrize("value", ["short", "https://youtube.com.evil.example/playlist?list=PL1234567890",
    "https://user@www.youtube.com/playlist?list=PL1234567890", "http://www.youtube.com/playlist?list=PL1234567890",
    "https://127.0.0.1/playlist?list=PL1234567890", "https://www.youtube.com/private?list=PL1234567890",
    "https://www.youtube.com/playlist?list=PL1234567890&list=PL2345678901", "https://www.youtube.com:443/playlist?list=PL1234567890"])
def test_invalid_links_never_trigger_requests(value):
    gateway, calls = make_gateway()
    with pytest.raises(UseCaseError) as failure:
        gateway.preview(value, actor_id=1)
    assert failure.value.status_code == 422 and not calls


def test_preview_uses_only_two_bounded_public_calls_and_keeps_credentials_out_of_urls_and_payloads():
    gateway, calls = make_gateway()
    preview = gateway.preview(IDENTIFIER, actor_id=1)
    assert len(calls) == 2 and preview["sample_only"] and len(preview["videos"]) == 1
    assert all(request.url.host == "www.googleapis.com" and "unit-test-private-key" not in str(request.url) for request in calls)
    assert all(request.headers["X-Goog-Api-Key"] == "unit-test-private-key" for request in calls)
    assert calls[1].url.params["maxResults"] == "12"
    assert "unit-test-private-key" not in str(preview) + str(gateway.status())
    assert "API original" not in str(gateway._previews)
    assert gateway.selected(preview["preview_id"], actor_id=1) == IDENTIFIER
    with pytest.raises(UseCaseError):
        gateway.selected(preview["preview_id"], actor_id=2)
    gateway._previews[preview["preview_id"]] = (0, 1, IDENTIFIER)
    with pytest.raises(UseCaseError) as expired:
        gateway.selected(preview["preview_id"], actor_id=1)
    assert expired.value.status_code == 409


def test_disabled_connector_never_connects_and_daily_budget_counts_attempts():
    gateway, calls = make_gateway(enabled=False)
    with pytest.raises(UseCaseError):
        gateway.preview(IDENTIFIER, actor_id=1)
    assert not calls and not gateway.status()["configured"]
    gateway, calls = make_gateway(limit=2)
    gateway.preview(IDENTIFIER, actor_id=1)
    with pytest.raises(UseCaseError) as limited:
        gateway.preview(IDENTIFIER, actor_id=1)
    assert limited.value.status_code == 429 and len(calls) == 2
    gateway._day = "2000-01-01"
    gateway.preview(IDENTIFIER, actor_id=1)
    assert len(calls) == 4 and gateway.status()["requests_used"] == 2


@pytest.mark.parametrize("response", [
    lambda request: httpx.Response(302, headers={"Location": "http://127.0.0.1/private"}),
    lambda request: httpx.Response(403, json={"error": {"message": "unit-test-private-key"}}),
    lambda request: httpx.Response(200, json={"items": "invalid"}),
    lambda request: httpx.Response(200, content=b" " * 300_001),
])
def test_provider_failures_are_sanitized_and_redirects_are_never_followed(response):
    gateway, calls = make_gateway(response=response)
    with pytest.raises(UseCaseError) as failure:
        gateway.preview(IDENTIFIER, actor_id=1)
    assert failure.value.status_code == 503 and "unit-test-private-key" not in failure.value.detail
    assert len(calls) == 1 and gateway.status()["requests_used"] == 1


def test_import_requires_admin_review_stores_only_editorial_fields_and_deduplicates(client):
    gateway, calls = make_gateway()
    client.app.dependency_overrides[get_youtube_learning] = lambda: gateway
    admin = administrator(client)
    _, candidate = register(client, "youtube-reader", skills=["excel"])
    assert client.get(PREFIX, headers=candidate).status_code == 403
    assert client.post(PREFIX + "/preview", headers=candidate, json={"url": IDENTIFIER}).status_code == 403
    assert not calls
    preview = client.post(PREFIX + "/preview", headers=admin, json={"url": IDENTIFIER}).json()
    editorial = {"title": "Excel para inventarios", "provider": "Not trusted", "url": "https://example.org/untrusted",
                 "instructions": "Prepara un registro de inventario con ejercicios seleccionados.", "hours": 3,
                 "skills": ["Excel"], "category": "administration", "cost": "paid",
                 "details": {"languages": ["es"], "certificate_cost": "free"}}
    payload = {"preview_id": preview["preview_id"], "editorial": editorial}
    result = client.post(PREFIX + "/import", headers=admin, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["created"] == 1
    course = next(row for row in result.json()["resources"] if row.get("source", {}).get("provider") == "youtube")
    assert not course["active"] and course["cost"] == "free" and course["details"]["certificate_cost"] == "none"
    assert course["title"] == editorial["title"] and course["url"] == preview["url"]
    assert "API original" not in str(course) and "API creator" not in str(course)
    assert client.post(PREFIX + "/import", headers=admin, json=payload).json()["created"] == 0
    assert not any(row.get("source", {}).get("provider") == "youtube" for row in client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"])
    content = {key: value for key, value in course.items() if key in editorial}
    content.update(active=True, version=course["version"])
    edited = client.put(f"/api/v1/admin/learning/resources/{course['id']}", headers=admin, json=content)
    assert edited.status_code == 200, edited.text
    visible = client.get("/api/v1/learning/catalog?area=all", headers=candidate).json()["resources"]
    assert any(row["id"] == course["id"] for row in visible)
    client.put(f"/api/v1/learning/plans/{course['id']}", headers=candidate, json={"status": "completed"}).raise_for_status()
    assert client.get("/api/v1/learning/passport", headers=candidate).json()["assessments"] == []
    with database_session.SessionLocal() as db:
        assert db.query(LearningResource).count() == 1
        assert "API original" not in str([row.content for row in db.query(LearningResource).all()])
        assert "unit-test-private-key" not in str([row.details for row in db.query(EventLog).all()])
    assert len(calls) == 2  # Catalog, plan and import never call Google.


def test_publication_is_explicit_and_invalid_preview_cannot_import(client):
    gateway, _ = make_gateway()
    client.app.dependency_overrides[get_youtube_learning] = lambda: gateway
    admin = administrator(client)
    preview = client.post(PREFIX + "/preview", headers=admin, json={"url": IDENTIFIER}).json()
    payload = {"preview_id": "x" * 32, "publish": True, "editorial": {"title": "Ruta Excel", "provider": "YouTube",
               "url": preview["url"], "instructions": "Practica con ejercicios de hojas de cálculo.", "hours": 2, "skills": ["excel"]}}
    assert client.post(PREFIX + "/import", headers=admin, json=payload).status_code == 409
    payload["preview_id"] = preview["preview_id"]
    result = client.post(PREFIX + "/import", headers=admin, json=payload)
    assert result.status_code == 200
    assert next(row for row in result.json()["resources"] if row.get("source", {}).get("provider") == "youtube")["active"]
