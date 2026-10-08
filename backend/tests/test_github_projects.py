# ruff: noqa: F811
import base64
from types import SimpleNamespace

import httpx
import pytest
from test_account_security import browser, csrf, login  # noqa: F401
from test_api_flows import client, register  # noqa: F401

from app.api.deps import get_repository_inspector
from app.application.errors import UseCaseError
from app.infrastructure.github_projects import GitHubProjectInspector

SHA = "a" * 40
TREE = "b" * 40
BLOB = "c" * 40


def adapter(fault=None):
    requests = []
    raw = b'{"dependencies":{"react":"19"}}'
    def handle(request):
        requests.append(str(request.url))
        assert request.url.host == "api.github.com" and "Authorization" not in request.headers
        if fault == "response_size":
            return httpx.Response(200, content=b"x" * 1_000_001)
        if fault in {"redirect", "rate", "private"}:
            return httpx.Response({"redirect": 302, "rate": 403, "private": 404}[fault], headers={"Location": "http://127.0.0.1/private"})
        if request.url.path.endswith("commits/HEAD"):
            return httpx.Response(200, json={"sha": SHA, "commit": {"tree": {"sha": TREE}}})
        if "/git/trees/" in request.url.path:
            rows = [{"path": "src/main.ts", "type": "blob", "mode": "100644", "sha": "d" * 40, "size": 500},
                    {"path": "package.json", "type": "blob", "mode": "100644", "sha": BLOB, "size": len(raw)},
                    {"path": ".env", "type": "blob", "mode": "100644", "sha": "e" * 40, "size": 50},
                    {"path": "malicious-link.py", "type": "blob", "mode": "120000", "sha": "f" * 40, "size": 20}]
            if fault == "path": rows[0]["path"] = "../main.ts"
            if fault == "manifest_size": rows[1]["size"] = 300000
            if fault == "count": rows = rows * 501
            return httpx.Response(200, json={"truncated": fault == "truncated", "tree": rows})
        assert request.url.path.endswith(f"/git/blobs/{BLOB}")
        return httpx.Response(200, json={"sha": BLOB, "encoding": "base64", "content": "!" if fault == "base64" else base64.b64encode(raw).decode()})
    return GitHubProjectInspector(SimpleNamespace(github_project_analysis_enabled=True), httpx.MockTransport(handle)), requests


def test_public_reader_is_commit_pinned_reads_only_manifests_and_never_uses_social_tokens():
    inspector, requests = adapter()
    report = inspector.inspect("https://github.com/demo/project.git")
    assert {row["skill"] for row in report["signals"]} == {"react", "typescript"}
    assert report["repository_url"] == "https://github.com/demo/project" and report["revision"] == SHA
    assert report["manifests_read"] == 1 and report["files_ignored"] == 1
    assert len(requests) == 3 and all("d" * 40 not in url and "f" * 40 not in url for url in requests)


@pytest.mark.parametrize("url", ["http://github.com/demo/project", "https://attacker.invalid/demo/project", "https://github.com@127.0.0.1/demo/project", "https://github.com/demo/project/tree/main", "https://github.com/demo/project?redirect=other", "https://github.com/demo/..", "https://github.com/demo/%2e%2e"])
def test_repository_url_cannot_choose_network_endpoint(url):
    inspector, requests = adapter()
    with pytest.raises(UseCaseError) as error:
        inspector.inspect(url)
    assert error.value.status_code == 422 and requests == []


@pytest.mark.parametrize("fault", ["redirect", "rate", "private", "path", "manifest_size", "count", "truncated", "base64", "response_size"])
def test_remote_failures_and_oversized_or_incomplete_projects_are_rejected(fault):
    inspector, requests = adapter(fault)
    with pytest.raises(UseCaseError) as error:
        inspector.inspect("https://github.com/demo/project")
    assert error.value.status_code == (503 if fault == "rate" else 422)
    assert all(url.startswith("https://api.github.com/") for url in requests)


def test_disabled_reader_makes_no_request():
    inspector, requests = adapter()
    inspector.settings.github_project_analysis_enabled = False
    with pytest.raises(UseCaseError) as error:
        inspector.inspect("https://github.com/demo/project")
    assert error.value.status_code == 503 and requests == []


def test_browser_consent_csrf_and_existing_evidence_flow(browser):
    register(browser, "alex")
    login(browser)
    inspector, requests = adapter()
    browser.app.dependency_overrides[get_repository_inspector] = lambda: inspector
    endpoint = "/api/v1/matching/projects/github/preview"
    payload = {"url": "https://github.com/demo/project", "confirm_public_access": True}
    assert browser.post(endpoint, json=payload).status_code == 403
    assert browser.post(endpoint, headers=csrf(browser), json={**payload, "confirm_public_access": False}).status_code == 422
    assert requests == []
    preview = browser.post(endpoint, headers=csrf(browser), json=payload)
    assert preview.status_code == 200, preview.text
    saved = browser.post("/api/v1/matching/projects/evidence", headers=csrf(browser), json={"preview_token": preview.json()["preview_token"],
        "title": "Mi proyecto público", "description": "Contribuí al código y puedo explicar sus decisiones.", "skills": ["react"], "confirm_ownership": True,
        "url": "https://unrelated.example.com", "add_to_profile": False})
    assert saved.status_code == 200, saved.text
    assert saved.json()[0]["url"] == "https://github.com/demo/project" and saved.json()[0]["verified"] is False
    assert saved.json()[0]["analysis"]["revision"] == SHA
