# ruff: noqa: F811
from test_api_flows import client, company_account, register  # noqa: F401

from app.api.deps import get_career_writer

BASE = "/api/v1/profiles/me"


def test_external_experience_requires_consent_and_stays_a_private_reversible_draft(client):
    _, headers = register(client, "external-writing", profession="Analista", skills=["Excel"])
    profile = client.get(BASE, headers=headers).json()
    profile["experiences"] = [{"role": "Analista", "company": "Organización privada", "description": "Apoyo en actualización de registros con Excel", "start_date": "2020-01", "end_date": "2022-01"}]
    client.put(BASE, headers=headers, json=profile).raise_for_status()
    before = client.get(BASE, headers=headers).json()
    observed = []
    class Writer:
        method = "groq-ai"
        external = True
        def generate(self, record, **kwargs):
            observed.append(record)
            return {"actions": [{"index": 0, "text": "Apoyé la actualización de registros con Excel."}], "idea": "¿Qué registros actualizaste?"}
    client.app.dependency_overrides[get_career_writer] = lambda: Writer()
    state = client.get(BASE + "/coach", headers=headers).json()
    payload = {"experience_index": 0, "source_version": state["source_version"]}
    assert client.post(BASE + "/coach/writing/generate", headers=headers, json=payload).status_code == 422
    assert observed == []
    payload["external_ai_consent"] = True
    response = client.post(BASE + "/coach/writing/generate", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    proposal = response.json()
    assert proposal["method"] == "groq-ai" and proposal["external_ai_consent_at"]
    assert "Organización privada" in observed[0]["_private_terms"]
    assert "_private_terms" not in str(proposal) and "_owner_id" not in str(proposal)
    assert client.get(BASE, headers=headers).json() == before
    endpoint = BASE + "/coach/writing/" + proposal["id"]
    client.put(endpoint, headers=headers, json={"action": "apply"}).raise_for_status()
    assert client.get(BASE, headers=headers).json()["experiences"][0]["description"] == proposal["after"]
    client.put(endpoint, headers=headers, json={"action": "undo"}).raise_for_status()
    assert client.get(BASE, headers=headers).json()["experiences"][0]["description"] == before["experiences"][0]["description"]


def test_external_summary_requires_consent_for_unsaved_facts_without_saving_them(client):
    _, headers = register(client, "external-summary", profession="Analista", skills=["Excel"])
    observed = []
    class Writer:
        method = "groq-ai"
        external = True
        def generate_summary(self, facts, **kwargs):
            observed.append(facts)
            return {"summary": "Soy analista con conocimientos de Excel. Apoyo la actualización de registros con Excel."}
    client.app.dependency_overrides[get_career_writer] = lambda: Writer()
    before = client.get(BASE, headers=headers).json()
    payload = {"profile": {"profession": "Analista", "skills": ["Excel"], "experience": "Apoyo la actualización de registros con Excel"}}
    assert client.post(BASE + "/summary/generate", headers=headers, json=payload).status_code == 422
    assert not observed
    payload["external_ai_consent"] = True
    response = client.post(BASE + "/summary/generate", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["method"] == "groq-ai" and observed[0]["_owner_id"]
    assert client.get(BASE, headers=headers).json() == before


def test_writing_service_discloses_only_safe_status_and_is_candidate_only(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "career_writer_provider", "groq")
    _, headers = register(client, "writer-status")
    response = client.get(BASE + "/writing-service", headers=headers)
    assert response.status_code == 200
    assert set(response.json()) == {"name", "provider", "external", "available", "summary_available"}
    assert response.json()["external"] and not response.json()["available"]
    assert client.get(BASE + "/writing-service").status_code == 401
    _, company = company_account(client, "writer-company")
    assert client.get(BASE + "/writing-service", headers=company).status_code == 403


def test_automatic_health_checks_only_provider_metadata_not_candidate_generation(client, monkeypatch):
    import httpx
    from pydantic import SecretStr

    from app.core.config import settings
    from app.infrastructure import integration_health

    for key, value in {"career_writer_provider": "groq", "groq_api_key": SecretStr("synthetic-health-key"),
                       "groq_free_plan_confirmed": True, "groq_zero_data_retention_confirmed": True,
                       "gmail_mail_enabled": False, "calendar_sync_enabled": False, "youtube_learning_enabled": False,
                       "oauth_google_client_id": "", "oauth_github_client_id": "", "oauth_linkedin_client_id": ""}.items():
        monkeypatch.setattr(settings, key, value)
    calls = []
    def serve(request):
        calls.append((request.method, str(request.url), request.content))
        return httpx.Response(200, json={"data": [{"id": "openai/gpt-oss-20b"}]})
    original = httpx.Client
    monkeypatch.setattr(integration_health, "SessionLocal", client.session_factory)
    monkeypatch.setattr(integration_health.httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(serve), **kwargs))
    rows = integration_health.cycle()
    assert calls == [("GET", "https://api.groq.com/openai/v1/models", b"")]
    assert rows[0]["provider"] == "career_writer" and rows[0]["state"] == "available"
    assert "synthetic-health-key" not in str(rows)
