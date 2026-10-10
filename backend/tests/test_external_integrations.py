# ruff: noqa: F811
import json
import time
from types import SimpleNamespace

import httpx
import pytest
from pydantic import ValidationError
from test_api_flows import client, register  # noqa: F401
from test_ecosystem import administrator
from test_github_projects import adapter

from app.api.deps import get_learn_catalog, get_repository_inspector
from app.application.errors import UseCaseError
from app.application.ports.services import MailDeliveryError
from app.core.config import Settings
from app.infrastructure.learn_catalog import BASE, VERSION, LearnCatalog
from app.infrastructure.security.resend import ResendDelivery

TENANT = "11111111-1111-1111-1111-111111111111"
APP = "22222222-2222-2222-2222-222222222222"
MODULE = {"id": "learn.demo.sql", "type": "module", "title": "Consultas SQL",
          "summary": "Practica consultas SQL y relaciones entre tablas.", "durationInMinutes": 45,
          "url": "https://learn.microsoft.com/training/modules/sql/", "locale": "es-es",
          "products": [{"id": "sql-server", "name": "SQL Server"}], "updatedAt": "2026-10-01T00:00:00Z"}


def learn_adapter(*, fault=None):
    requests = []
    def handle(request):
        requests.append(request)
        if request.url.host == "login.microsoftonline.com":
            assert request.url.path == f"/{TENANT}/oauth2/v2.0/token"
            assert b"https%3A%2F%2Flearn.microsoft.com%2F.default" in request.content
            return httpx.Response(200, json={"access_token": "PRIVATE-TOKEN", "expires_in": 3600})
        assert request.url.host == "learn.microsoft.com"
        assert request.headers["Authorization"] == "Bearer PRIVATE-TOKEN"
        assert request.url.params["api-version"] == VERSION
        if fault == "network": raise httpx.ReadTimeout("PRIVATE-SECRET")
        if fault == "status": return httpx.Response(401, text="PRIVATE-SECRET")
        if fault == "redirect": return httpx.Response(302, headers={"Location": "https://evil.invalid/steal"})
        if fault == "oversized": return httpx.Response(200, content=b"x" * 2_000_001)
        if fault == "malformed": return httpx.Response(200, content=b"not json")
        if fault == "invalid_rows": return httpx.Response(200, json={"value": [{**MODULE, "url": "https://evil.invalid/course"}, {**MODULE, "durationInMinutes": 0}, MODULE]})
        return httpx.Response(200, json={"value": [MODULE], "nextLink": "https://evil.invalid/steal" if fault == "next_link" else f"{BASE}/modules?api-version={VERSION}&skiptoken=opaque"})
    settings = SimpleNamespace(learn_enabled=True, learn_tenant_id=TENANT, learn_client_id=APP, learn_client_secret="PRIVATE-SECRET")
    return LearnCatalog(settings, httpx.MockTransport(handle)), requests


def resend_adapter(status=200):
    requests = []
    def handle(request):
        requests.append(request)
        if status == "timeout": raise httpx.ReadTimeout("PRIVATE-SECRET")
        return httpx.Response(status, json={"id": "delivery-id", "message": "PRIVATE-SECRET"}, headers={"Location": "https://evil.invalid/steal"})
    settings = SimpleNamespace(resend_enabled=True, resend_api_key="PRIVATE-KEY", resend_from="access@example.com", secret_key="s" * 48)
    return ResendDelivery(settings, httpx.MockTransport(handle)), requests


def send(gateway, message_id=1):
    gateway.send(recipient="recipient@example.com", subject="Acceso", body="PRIVATE-LINK", message_id=message_id)


def test_resend_fixed_origin_plain_text_and_stable_private_idempotency():
    gateway, requests = resend_adapter()
    send(gateway); send(gateway); send(gateway, 2)
    assert all(str(row.url) == "https://api.resend.com/emails" for row in requests)
    assert requests[0].headers["Idempotency-Key"] == requests[1].headers["Idempotency-Key"]
    assert requests[0].headers["Idempotency-Key"] != requests[2].headers["Idempotency-Key"]
    assert json.loads(requests[0].content) == {"from": "access@example.com", "to": ["recipient@example.com"], "subject": "Acceso", "text": "PRIVATE-LINK"}
    assert requests[0].headers["Authorization"] == "Bearer PRIVATE-KEY"
    gateway.settings.resend_enabled = False
    with pytest.raises(MailDeliveryError): send(gateway)
    assert len(requests) == 3


@pytest.mark.parametrize("status,retryable,kind", [(401, False, "configuration"), (403, False, "configuration"),
    (422, False, "permanent"), (302, False, "permanent"), (429, True, "temporary"), (503, True, "temporary"), ("timeout", True, "transport")])
def test_resend_sanitizes_errors_and_never_follows_redirects(status, retryable, kind):
    gateway, requests = resend_adapter(status)
    with pytest.raises(MailDeliveryError) as error: send(gateway)
    assert error.value.retryable == retryable and error.value.kind == kind
    assert "PRIVATE" not in str(error.value) and error.value.__cause__ is None
    assert len(requests) == 1


@pytest.mark.parametrize("overrides", [{"resend_api_key": ""}, {"resend_from": "invalid"}, {"local_mail_enabled": True}, {"smtp_enabled": True}])
def test_resend_rejects_ambiguous_or_incomplete_configuration(overrides):
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, secret_key="s" * 48, **(dict(resend_enabled=True, resend_api_key="PRIVATE-KEY", resend_from="access@example.com") | overrides))
    assert "PRIVATE-KEY" not in str(error.value)


def test_resend_queue_mode_and_learn_configuration():
    config = Settings(_env_file=None, secret_key="s" * 48, resend_enabled=True, resend_api_key="PRIVATE-KEY", resend_from="access@example.com",
                      learn_enabled=True, learn_tenant_id=TENANT, learn_client_id=APP, learn_client_secret="PRIVATE-SECRET")
    assert config.mail_delivery_enabled and config.mail_delivery_mode == "pending"
    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="s" * 48, learn_enabled=True, learn_tenant_id="../attacker", learn_client_id=APP, learn_client_secret="PRIVATE-SECRET")


def test_learn_preview_is_bounded_authenticated_and_tokens_are_not_returned():
    gateway, requests = learn_adapter()
    first = gateway.preview(actor_id=1, products="sql-server")
    content = first["resources"][0]["content"]
    assert content["hours"] == 0.75 and not content["active"] and content["skills"] == ["sql server"]
    assert requests[1].url.params["maxpagesize"] == "20" and requests[1].url.params["locale"] == "es-es"
    gateway.preview(actor_id=1, cursor=first["next_cursor"])
    assert len(requests) == 3  # second page reuses a nonexpired token
    assert "PRIVATE" not in str(first)
    with pytest.raises(UseCaseError) as error: gateway.selected(first["preview_id"], [MODULE["id"]], actor_id=2)
    assert error.value.status_code == 409
    with pytest.raises(UseCaseError): gateway.selected(first["preview_id"], ["injected-course"], actor_id=1)
    selected = gateway.selected(first["preview_id"], [MODULE["id"]], actor_id=1)
    selected[0]["content"]["active"] = True
    assert not gateway.selected(first["preview_id"], [MODULE["id"]], actor_id=1)[0]["content"]["active"]
    expiry, owner, rows, fetched = gateway._previews[first["preview_id"]]
    gateway._previews[first["preview_id"]] = (time.monotonic() - 1, owner, rows, fetched)
    with pytest.raises(UseCaseError): gateway.selected(first["preview_id"], [MODULE["id"]], actor_id=1)


@pytest.mark.parametrize("fault", ["network", "status", "redirect", "oversized", "malformed", "next_link"])
def test_learn_does_not_expose_secrets_or_follow_provider_urls(fault):
    gateway, requests = learn_adapter(fault=fault)
    with pytest.raises(UseCaseError) as error: gateway.preview(actor_id=1)
    assert error.value.status_code in {422, 503} and "PRIVATE" not in error.value.detail
    assert len(requests) == 2


def test_learn_disabled_and_forged_pagination_make_no_network_calls():
    gateway, requests = learn_adapter()
    with pytest.raises(UseCaseError): gateway.preview(actor_id=1, cursor="https://learn.microsoft.com@evil.invalid/api/v1/modules")
    gateway.settings.learn_enabled = False
    with pytest.raises(UseCaseError): gateway.preview(actor_id=1)
    assert not requests
    gateway, _ = learn_adapter(fault="invalid_rows")
    result = gateway.preview(actor_id=1)
    assert result["skipped"] == 2 and len(result["resources"]) == 1


def test_admin_import_is_a_draft_deduplicated_and_preserves_edits(client):
    gateway, requests = learn_adapter()
    client.app.dependency_overrides[get_learn_catalog] = lambda: gateway
    admin = administrator(client)
    _, candidate = register(client, "learn-candidate")
    root = "/api/v1/admin/learning/sources"
    for method, path, payload in [("GET", root, None), ("POST", root + "/microsoft-learn/preview", {}),
        ("POST", root + "/microsoft-learn/import", {"preview_id": "x" * 24, "ids": [MODULE["id"]]})]:
        assert client.request(method, path, headers=candidate, **({"json": payload} if payload is not None else {})).status_code == 403
    assert requests == []
    preview = client.post(root + "/microsoft-learn/preview", headers=admin, json={}).json()
    payload = {"preview_id": preview["preview_id"], "ids": [MODULE["id"]]}
    result = client.post(root + "/microsoft-learn/import", headers=admin, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["created"] == 1
    row = next(row for row in result.json()["resources"] if row.get("source", {}).get("provider") == "microsoft_learn")
    assert not row["active"] and row["source"]["id"] == MODULE["id"] and row["source"]["fetched_at"]
    assert row["id"] not in [item["id"] for item in client.get("/api/v1/learning/catalog", headers=candidate).json()["resources"]]
    content = {key: row[key] for key in ["category", "title", "provider", "kind", "instructions", "url", "skills", "hours", "cost", "sponsored", "affiliate", "disclosure", "active", "version"]}
    content.update(active=True, skills=["sql"], title="Curso revisado por administración")
    edited = client.put(f"/api/v1/admin/learning/resources/{row['id']}", headers=admin, json=content)
    assert edited.status_code == 200, edited.text
    imported = client.post(root + "/microsoft-learn/import", headers=admin, json=payload).json()
    assert imported["created"] == 0 and imported["existing"] == 1
    updated = next(item for item in imported["resources"] if item["id"] == row["id"])
    assert updated["title"] == content["title"] and updated["active"] and updated["source"] == row["source"]


def test_github_cache_is_private_copy_and_disabling_prevents_cache_access():
    gateway, requests = adapter()
    report = gateway.inspect("https://github.com/demo/project")
    report["signals"].clear()
    assert gateway.inspect("https://github.com/demo/project")["signals"] and len(requests) == 3
    gateway.settings.github_project_analysis_enabled = False
    with pytest.raises(UseCaseError): gateway.inspect("https://github.com/demo/project")
    assert len(requests) == 3


def test_github_local_hourly_budget_blocks_before_network():
    gateway, requests = adapter()
    gateway._calls.extend([time.monotonic()] * 50)
    with pytest.raises(UseCaseError) as error: gateway.inspect("https://github.com/demo/project")
    assert error.value.status_code == 503 and not requests


def test_github_candidate_preview_requires_consent_and_saves_only_selected_signals(client):
    gateway, requests = adapter()
    client.app.dependency_overrides[get_repository_inspector] = lambda: gateway
    _, candidate = register(client, "project-candidate", skills=["python"])
    _, other = register(client, "project-outsider")
    admin = administrator(client)
    root = "/api/v1/integrations/github"
    assert client.post(root + "/preview", headers=admin, json={"url": "https://github.com/demo/project", "confirm_public_access": True}).status_code == 403
    assert client.post(root + "/preview", headers=candidate, json={"url": "https://github.com/demo/project", "confirm_public_access": False}).status_code == 422
    assert not requests
    response = client.post(root + "/preview", headers=candidate, json={"url": "https://github.com/demo/project", "confirm_public_access": True})
    assert response.status_code == 200, response.text
    preview = response.json()
    payload = {"preview_token": preview["preview_token"], "title": "Mi proyecto React", "description": "Construí los componentes de interfaz del proyecto.",
               "skills": ["react"], "confirm_ownership": True, "add_to_profile": False}
    assert client.post(root + "/evidence", headers=other, json=payload).status_code == 422
    assert client.post(root + "/evidence", headers=candidate, json=payload | {"skills": ["invented-skill"]}).status_code == 422
    result = client.post(root + "/evidence", headers=candidate, json=payload)
    assert result.status_code == 200, result.text
    row = result.json()[-1]
    assert row["url"] == "https://github.com/demo/project" and row["analysis"]["origin"] == "github_public"
    assert not row["verified"] and not row["add_to_profile"] and row["skills"] == ["react"]
    assert client.post(root + "/evidence", headers=candidate, json=payload).status_code == 409
    assert client.get("/api/v1/matching/evidence", headers=other).json() == []
