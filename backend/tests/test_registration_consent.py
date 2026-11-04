# ruff: noqa: F401, F811
from datetime import datetime, timezone

import pytest
from test_account_security import browser, csrf, login
from test_api_flows import client, legal_acceptance, register
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


def pending_company(browser):
    account, _ = register(browser, "company-setup", "company", company_name="Empresa de ejemplo", nit="SETUP-DEMO")
    with browser.session_factory() as db:
        user = db.get(User, account["id"])
        user.email_verified = True
        user.registration_pending = True
        user.legal_acceptance = {}
        db.commit()
    assert login(browser, "company-setup@example.com", portal="company").status_code == 200
    return account["id"]


@pytest.mark.parametrize("decision", ["missing", "terms", "outdated", "unconfirmed", "blank_name"])
def test_provisioned_company_requires_explicit_current_decisions(browser, decision):
    account_id = pending_company(browser)
    payload = {"name": "Equipo de ejemplo", "confirmed": True, **legal_acceptance()}
    if decision == "missing":
        payload.pop("data_processing_accepted")
    elif decision == "terms":
        payload["terms_accepted"] = False
    elif decision == "outdated":
        payload["privacy_version"] = "obsolete"
    elif decision == "unconfirmed":
        payload["confirmed"] = False
    else:
        payload["name"] = "  "
    assert browser.post("/api/v1/auth/company/registration/complete", headers=csrf(browser), json=payload).status_code == 422
    with browser.session_factory() as db:
        user = db.get(User, account_id)
        assert user.registration_pending and user.legal_acceptance == {}
    assert browser.get("/api/v1/companies/me").status_code == 403


def test_company_first_access_records_once_and_preserves_security_gates(browser):
    account_id = pending_company(browser)
    endpoint = "/api/v1/auth/company/registration/complete"
    payload = {"name": "  Equipo  de ejemplo  ", "confirmed": True, **legal_acceptance()}
    assert browser.post(endpoint, json=payload).status_code == 403
    assert browser.post(endpoint, headers={**csrf(browser), "Origin": "https://untrusted.example"}, json=payload).status_code == 403
    response = browser.post(endpoint, headers=csrf(browser), json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Equipo de ejemplo"
    assert response.json()["registration_pending"] is False
    assert response.json()["role"] == "company"
    with browser.session_factory() as db:
        user = db.get(User, account_id)
        evidence = user.legal_acceptance
        assert evidence["channel"] == "company_setup" and len(evidence["notice_sha256"]) == 64
        assert evidence["terms_accepted"] is evidence["data_processing_accepted"] is True
        company = db.query(Company).one()
        assert company.verification_required and company.verification_status == "pending"
    # Completing the account does not bypass the authenticator or legal company review.
    response = browser.get("/api/v1/companies/me")
    assert response.status_code == 403 and "dos factores" in response.json()["detail"]
    assert browser.post(endpoint, headers=csrf(browser), json=payload).status_code == 409
    with browser.session_factory() as db:
        assert db.get(User, account_id).legal_acceptance == evidence


def test_candidate_cannot_use_company_setup(browser):
    register(browser, "candidate-setup")
    assert login(browser, "candidate-setup@example.com").status_code == 200
    response = browser.post("/api/v1/auth/company/registration/complete", headers=csrf(browser),
                            json={"name": "Equipo de ejemplo", "confirmed": True, **legal_acceptance()})
    assert response.status_code == 403
