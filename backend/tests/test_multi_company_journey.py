"""Several industries with independent browser sessions and real MFA."""
# ruff: noqa: F811
from fastapi.testclient import TestClient
from test_account_security import browser  # noqa: F401
from test_api_flows import client, register  # noqa: F401
from test_local_acceptance import PASSWORD, confirm_mail, enroll_mfa, request

from app.infrastructure.database.models import Company


def test_three_companies_cannot_edit_other_vacancies_and_match_different_profiles(browser):
    cases = [("ventas", "Asesor comercial", ["ventas", "comunicacion"], "Ventas y comercio"),
             ("finanzas", "Auxiliar contable", ["contabilidad", "conciliacion bancaria"], "Finanzas y banca"),
             ("salud", "Auxiliar administrativa en salud", ["confidencialidad", "gestion documental"], "Salud y bienestar")]
    records = []
    for key, title, skills, sector in cases:
        with TestClient(browser.app) as employer, TestClient(browser.app) as candidate:
            owner, _ = register(employer, "multi-" + key, "company", company_name=f"Ficticia {key}", nit="MULTI-" + key)
            employee, _ = register(candidate, "person-" + key, skills=skills[:1], profession=title)
            request(employer, "POST", "/auth/session/company/login", json={"email": owner["email"], "password": PASSWORD})
            recovery = enroll_mfa(employer)
            confirm_mail(employer, owner["email"])
            with browser.session_factory() as db:
                company = db.query(Company).filter_by(owner_user_id=owner["id"]).one()
                company.verification_status = "verified"
                db.commit()
            job = request(employer, "POST", "/jobs", expected=201, json={"title": title, "description": f"Apoya al equipo como {title}. Registra actividades y comunica resultados de forma clara.", "requirements": "Habilidades: " + ", ".join(skills), "skills": skills, "sector": sector})
            request(candidate, "POST", "/auth/session/candidate/login", json={"email": employee["email"], "password": PASSWORD})
            confirm_mail(candidate, employee["email"])
            catalog = request(candidate, "GET", "/learning/catalog")
            assert any(row["category"] == {"ventas": "sales", "finanzas": "finance", "salud": "care"}[key] for row in catalog["resources"])
            request(candidate, "POST", "/applications", expected=201, json={"job_id": job["id"]})
            records.append((owner, recovery, job))
    for owner, recovery, job in records:
        with TestClient(browser.app) as employer:
            request(employer, "POST", "/auth/session/company/login", json={"email": owner["email"], "password": PASSWORD, "code": recovery})
            owned = [row for row in request(employer, "GET", "/jobs?status=") if row["company_id"] == job["company_id"]]
            assert [row["id"] for row in owned] == [job["id"]]
            for _, _, other_job in records:
                if other_job["id"] != job["id"]:
                    response = employer.patch(f"/api/v1/jobs/{other_job['id']}", headers={"X-CSRF-Token": employer.cookies.get("talentsync_csrf")}, json={"status": "paused"})
                    assert response.status_code in {403, 404}
