# ruff: noqa: F401, F811
from datetime import datetime, timezone

import pytest
from test_account_security import browser, csrf
from test_api_flows import client, legal_acceptance
from test_social_access import callback, social, start

from app.application.use_cases.legal_consent import DOCUMENTS
from app.infrastructure.database.models import Company, Profile, User


@pytest.mark.parametrize("endpoint,role", [("register", "candidate"), ("candidate/register", "candidate"), ("company/register", "company")])
@pytest.mark.parametrize("decision", ["missing", "data", "terms", "string", "outdated"])
def test_registration_requires_current_explicit_decisions(client, endpoint, role, decision):
    payload = {"name": "Persona de revisión", "email": "consent@example.com", "password": "Test-password-2026!",
               "role": role, "company_name": "Empresa de revisión", "nit": "CONSENT-1", **legal_acceptance()}
    if decision == "missing":
        for field in legal_acceptance():
            payload.pop(field)
    elif decision == "data":
        payload["data_processing_accepted"] = False
    elif decision == "terms":
        payload["terms_accepted"] = False
    elif decision == "string":
        payload["terms_accepted"] = "true"
    else:
        payload["privacy_version"] = "obsolete"
    assert client.post(f"/api/v1/auth/{endpoint}", json=payload).status_code == 422
    with client.session_factory() as db:
        assert db.query(User).count() == db.query(Company).count() == db.query(Profile).count() == 0


@pytest.mark.parametrize("role", ["candidate", "company"])
def test_server_records_the_actual_consent_and_ignores_forged_evidence(client, role):
    before = datetime.now(timezone.utc)
    response = client.post(f"/api/v1/auth/{role}/register", json={
        "name": "Persona de revisión", "email": "consent@example.com", "password": "Test-password-2026!",
        "role": role, "company_name": "Empresa de revisión", "nit": "CONSENT-1", **legal_acceptance(),
        "legal_acceptance": {"accepted_at": "1900-01-01", "channel": "forged"},
    })
    assert response.status_code == 201, response.text
    with client.session_factory() as db:
        evidence = db.get(User, response.json()["id"]).legal_acceptance
        assert before <= datetime.fromisoformat(evidence["accepted_at"]) <= datetime.now(timezone.utc)
        assert evidence["privacy_version"] == DOCUMENTS["privacy_version"]
        assert evidence["terms_version"] == DOCUMENTS["terms_version"]
        assert evidence["channel"] == "email" and len(evidence["notice_sha256"]) == 64
        assert DOCUMENTS["data_processing_notice"] in evidence["notice"]
        assert evidence["data_processing_accepted"] is evidence["terms_accepted"] is True


@pytest.mark.parametrize("provider", ["google", "github"])
def test_social_account_cannot_finish_without_consent_and_records_it_once(social, provider):
    callback(social, start(social, provider), provider)
    endpoint = "/api/v1/auth/social/registration"
    payload = {"name": "Persona de Revisión", "profession": "Analista", "confirmed": True}
    for decision in [{}, {**legal_acceptance(), "terms_accepted": False}, {**legal_acceptance(), "terms_version": "obsolete"}]:
        assert social.post(endpoint, headers=csrf(social), json={**payload, **decision}).status_code == 422
        with social.session_factory() as db:
            user = db.query(User).one()
            assert user.registration_pending is True and user.legal_acceptance == {}
    assert social.post(endpoint, headers=csrf(social), json={**payload, **legal_acceptance()}).status_code == 200
    with social.session_factory() as db:
        evidence = db.query(User).one().legal_acceptance
        assert evidence["channel"] == "social" and evidence["terms_accepted"] is True
    assert social.post(endpoint, headers=csrf(social), json={**payload, **legal_acceptance()}).status_code == 409
    with social.session_factory() as db:
        assert db.query(User).one().legal_acceptance == evidence
