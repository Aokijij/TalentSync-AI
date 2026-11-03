# ruff: noqa: F811
import copy
import json
import time
from types import SimpleNamespace

import httpx
import pytest
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator

from app.api.deps import get_account_security, get_codewars_reader
from app.application.errors import UseCaseError
from app.core.config import settings
from app.infrastructure.codewars import CodewarsReader
from app.infrastructure.database.models import User

PROFILE = {"username": "practice-demo", "name": "UNNEEDED-NAME", "clan": "UNNEEDED-CLAN",
           "skills": ["invented-skill"], "ranks": {"overall": {"rank": -5, "score": 350},
           "languages": {"python": {"rank": -5, "score": 350}, "javascript": {"rank": -8, "score": 0},
                         "csharp": {"rank": -8, "score": 2}}}, "codeChallenges": {"totalCompleted": 20}}
ROOT = "/api/v1/integrations/codewars"


def adapter(*, fault=None, profile=None):
    calls = []
    def handle(request):
        calls.append(request)
        assert request.url.host == "www.codewars.com"
        assert request.url.path.startswith("/api/v1/users/")
        assert "authorization" not in request.headers
        if fault == "timeout": raise httpx.ReadTimeout("PRIVATE PROVIDER ERROR")
        if fault == "oversize": return httpx.Response(200, content=b"x" * 131073)
        if fault == "malformed": return httpx.Response(200, content=b"PRIVATE PROVIDER ERROR")
        if isinstance(fault, int): return httpx.Response(fault, text="PRIVATE PROVIDER ERROR", headers={"Location": "https://evil.invalid/steal"})
        return httpx.Response(200, json=profile if profile is not None else PROFILE)
    return CodewarsReader(SimpleNamespace(codewars_enabled=True), httpx.MockTransport(handle)), calls


def test_public_profile_maps_only_ranked_languages_and_cache_is_immutable():
    reader, calls = adapter()
    report = reader.inspect("practice-demo")
    assert report["overall"] == {"rank": "5 kyu", "score": 350} and report["completed_challenges"] == 20
    assert report["signals"] == [{"skill": "c#", "rank": "8 kyu", "score": 2}, {"skill": "python", "rank": "5 kyu", "score": 350}]
    assert all(secret not in str(report) for secret in ["UNNEEDED", "invented-skill"])
    report["signals"].clear()
    assert reader.inspect("practice-demo")["signals"] and len(calls) == 1
    reader.settings.codewars_enabled = False
    with pytest.raises(UseCaseError): reader.inspect("practice-demo")
    assert len(calls) == 1


@pytest.mark.parametrize("username", ["../admin", "https://codewars.com/users/demo", "a/b", "a?query", "a#fragment", "a%2fadmin", "", "a" * 81])
def test_invalid_username_never_reaches_network(username):
    reader, calls = adapter()
    with pytest.raises(UseCaseError) as error: reader.inspect(username)
    assert error.value.status_code == 422 and not calls


@pytest.mark.parametrize("fault,status", [(404, 422), (302, 503), (403, 503), (429, 503), (503, 503), ("timeout", 503), ("oversize", 503), ("malformed", 503)])
def test_provider_failures_are_sanitized_and_redirects_are_not_followed(fault, status):
    reader, calls = adapter(fault=fault)
    with pytest.raises(UseCaseError) as error: reader.inspect("demo")
    assert error.value.status_code == status and "PRIVATE" not in error.value.detail
    assert len(calls) == 1


def test_budget_blocks_before_network_and_cache_is_bounded():
    reader, calls = adapter()
    for index in range(33): reader.inspect(f"demo{index}")
    assert len(reader._cache) == 32
    reader._calls.extend([time.monotonic()] * 50)
    with pytest.raises(UseCaseError): reader.inspect("uncached")
    assert len(calls) == 33


def test_unranked_profile_is_valid_without_inventing_signals():
    value = {"username": "new-user", "ranks": {"overall": None, "languages": {}}, "codeChallenges": {"totalCompleted": 0}}
    reader, _ = adapter(profile=value)
    report = reader.inspect("new-user")
    assert report["signals"] == [] and report["overall"]["rank"] == "Sin rango"


@pytest.mark.parametrize("change", [
    {"username": "https://evil.invalid"}, {"ranks": "unexpected"},
    {"codeChallenges": {"totalCompleted": -1}}, {"codeChallenges": {"totalCompleted": True}},
    {"ranks": {"overall": {"rank": 99, "score": 3}}},
])
def test_malformed_profile_fails_safely(change):
    reader, _ = adapter(profile=PROFILE | change)
    with pytest.raises(UseCaseError) as error: reader.inspect("demo")
    assert error.value.status_code == 503


def test_api_consent_permissions_owner_selection_refresh_and_removal(client, monkeypatch):
    monkeypatch.setattr(settings, "codewars_enabled", True)
    reader, calls = adapter()
    client.app.dependency_overrides[get_codewars_reader] = lambda: reader
    user, candidate = register(client, "cw-candidate", skills=["sql"])
    _, outsider = register(client, "cw-outsider")
    _, company = register(client, "cw-company", role="company", company_name="Codewars empresa ficticia", nit="CW-DEMO-001")
    admin = administrator(client)
    request = {"username": "practice-demo", "confirm_public_access": True}
    for headers in [admin, company]:
        assert client.get(ROOT + "/capabilities", headers=headers).status_code == 403
        assert client.post(ROOT + "/preview", headers=headers, json=request).status_code == 403
    assert client.get(ROOT + "/capabilities", headers=candidate).json()["codewars_public"]
    assert client.post(ROOT + "/preview", headers=candidate, json=request | {"confirm_public_access": False}).status_code == 422
    assert not calls
    preview = client.post(ROOT + "/preview", headers=candidate, json=request).json()
    payload = {"preview_token": preview["preview_token"], "title": "Mi práctica en Codewars", "description": "Practico algoritmos y resolución de problemas en Python.",
               "skills": ["python"], "confirm_ownership": True, "url": "https://evil.invalid/forged", "add_to_profile": False}
    assert client.post(ROOT + "/evidence", headers=outsider, json=payload).status_code == 422
    assert client.post(ROOT + "/evidence", headers=admin, json=payload).status_code == 403
    assert client.post(ROOT + "/evidence", headers=candidate, json=payload | {"skills": ["invented-skill"]}).status_code == 422
    assert client.post(ROOT + "/evidence", headers=candidate, json=payload | {"confirm_ownership": False}).status_code == 422
    result = client.post(ROOT + "/evidence", headers=candidate, json=payload)
    assert result.status_code == 200, result.text
    row = result.json()[0]
    assert row["url"] == "https://www.codewars.com/users/practice-demo"
    assert row["analysis"]["origin"] == "codewars_public" and not row["verified"]
    with client.session_factory() as session: assert session.get(User, user["id"]).profile.skills == ["sql"]
    assert client.get("/api/v1/matching/evidence", headers=outsider).json() == []
    refreshed = client.post(ROOT + "/evidence", headers=candidate, json=payload | {"add_to_profile": True, "title": "Práctica actualizada"}).json()
    assert len(refreshed) == 1 and refreshed[0]["id"] == row["id"] and refreshed[0]["title"] == "Práctica actualizada"
    with client.session_factory() as session: assert set(session.get(User, user["id"]).profile.skills) == {"sql", "python"}
    assert client.delete(f"/api/v1/matching/evidence/{row['id']}", headers=candidate).status_code == 204
    assert client.get("/api/v1/matching/evidence", headers=candidate).json() == []
    with client.session_factory() as session: assert "python" in session.get(User, user["id"]).profile.skills


@pytest.mark.parametrize("change", [{"expires_at": 0}, {"issued_at": 9999999999}, {"purpose": "project-preview-v1"}])
def test_expired_future_and_cross_integration_previews_rejected(client, monkeypatch, change):
    monkeypatch.setattr(settings, "codewars_enabled", True)
    reader, _ = adapter()
    client.app.dependency_overrides[get_codewars_reader] = lambda: reader
    _, candidate = register(client, "cw-expiry")
    preview = client.post(ROOT + "/preview", headers=candidate, json={"username": "demo", "confirm_public_access": True}).json()
    security = get_account_security()
    envelope = json.loads(security.decrypt_secret(preview["preview_token"]))
    payload = {"preview_token": security.encrypt_secret(json.dumps(envelope | change)), "title": "Mi práctica", "description": "Practico algoritmos en Codewars.", "skills": ["python"], "confirm_ownership": True}
    assert client.post(ROOT + "/evidence", headers=candidate, json=payload).status_code == 422


def test_disabled_integration_blocks_save_of_existing_preview(client, monkeypatch):
    monkeypatch.setattr(settings, "codewars_enabled", True)
    reader, _ = adapter()
    client.app.dependency_overrides[get_codewars_reader] = lambda: reader
    _, candidate = register(client, "cw-disabled")
    preview = client.post(ROOT + "/preview", headers=candidate, json={"username": "demo", "confirm_public_access": True}).json()
    monkeypatch.setattr(settings, "codewars_enabled", False)
    payload = {"preview_token": preview["preview_token"], "title": "Mi práctica", "description": "Practico algoritmos en Codewars.", "skills": ["python"], "confirm_ownership": True}
    assert client.post(ROOT + "/evidence", headers=candidate, json=payload).status_code == 503


def test_snapshot_changes_with_activity_but_excludes_unneeded_personal_data():
    original = CodewarsReader._report(PROFILE)
    value = copy.deepcopy(PROFILE)
    value["codeChallenges"]["totalCompleted"] += 1
    assert CodewarsReader._report(value)["fingerprint"] != original["fingerprint"]
    value = PROFILE | {"name": "another-name", "clan": "another-clan", "skills": ["different"]}
    assert CodewarsReader._report(value)["fingerprint"] == original["fingerprint"]
