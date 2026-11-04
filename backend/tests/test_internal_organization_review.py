# ruff: noqa: F401, F811
from test_account_security import browser, login
from test_api_flows import client, company_account
from test_organizations import admin_account, verified_email

from app.infrastructure.database.models import Company


def test_internal_workspace_is_visible_and_cannot_be_legally_approved(client):
    owner, headers = company_account(client)
    verified_email(client, owner)
    admin = admin_account(client)
    company_id = client.get("/api/v1/organization/me", headers=headers).json()["id"]
    rows = client.get("/api/v1/admin/verification-queue", headers=admin).json()["items"]
    assert rows[0]["id"] == company_id and rows[0]["verification_kind"] == "internal"
    review = f"/api/v1/admin/verifications/{company_id}"
    assert client.post(review, headers=admin, json={"status": "verified", "feedback": "No hay registro legal para esta organización"}).status_code == 422
    assert client.post(review, headers=admin, json={"status": "internal_approved", "feedback": "Revisar primero la solicitud del responsable"}).status_code == 422
    payload = {"platform_url": "https://example.com", "business_activity": "Plataforma de empleo y aprendizaje", "responsible_name": "Responsable del espacio", "contact_email": "owner@example.com", "notes": "Solicito revisar la operación del espacio interno de la plataforma.", "accuracy_confirmed": True}
    assert client.post("/api/v1/organization/internal-review", headers=headers, json={**payload, "accuracy_confirmed": False}).status_code == 422
    assert client.post("/api/v1/organization/internal-review", headers=headers, json=payload).status_code == 200
    response = client.post(review, headers=admin, json={"status": "internal_approved", "feedback": "Propietario y enlace de la plataforma revisados"})
    assert response.status_code == 200, response.text
    summary = client.get("/api/v1/organization/me", headers=headers).json()
    assert summary["verification_required"] is False and summary["verification_status"] == "internal_approved"


def test_safe_welcome_metadata_is_available_before_authenticator_without_exposing_supports(browser):
    owner, _ = company_account(browser)
    with browser.session_factory() as db:
        company = db.query(Company).one()
        company.verification_submission = {"registry_document_url": "https://private.example.test/secret", "representative_name": "Private representative", "submitted_at": "2026-11-04"}
        db.commit()
    assert login(browser, owner["email"], portal="company").status_code == 200
    response = browser.get("/api/v1/organization/access")
    assert response.status_code == 200 and response.json()["role"] == "owner"
    assert "secret" not in response.text and "Private representative" not in response.text
    assert browser.get("/api/v1/organization/me").status_code == 403
