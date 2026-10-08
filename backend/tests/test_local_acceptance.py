"""Cross-role acceptance on a disposable database, using real session cookies and MFA."""
# ruff: noqa: F811
import re
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient
from test_account_security import browser  # noqa: F401
from test_api_flows import client, register  # noqa: F401

from app.domain.entities.enums import UserRole
from app.domain.services.authentication import totp
from app.infrastructure.database.models import Application, EventLog, User

PASSWORD = "Test-password-2026!"
SQL = "SELECT c.name AS customer, SUM(o.total) AS total FROM customers c JOIN orders o ON o.customer_id=c.id WHERE o.status='paid' GROUP BY c.id,c.name HAVING SUM(o.total)>=100"


def request(actor, method, path, *, expected=200, **kwargs):
    headers = {"X-CSRF-Token": actor.cookies.get("talentsync_csrf", ""), **kwargs.pop("headers", {})}
    response = actor.request(method, "/api/v1" + path, headers=headers, **kwargs)
    assert response.status_code == expected, (method, path, response.status_code, response.text)
    return response.json() if response.content else None


def sign_in(actor, email, *, admin=False, code=None):
    return request(actor, "POST", "/auth/session/" + ("admin/login" if admin else "login"),
                   json={"email": email, "password": PASSWORD, "code": code})


def confirm_mail(actor, email):
    mail = next(row for row in request(actor, "GET", "/dev/mailbox") if row["recipient"] == email)
    link = re.search(r"https?://\S+", mail["body"]).group()
    token = parse_qs(urlsplit(link).query)["token"][0]
    request(actor, "POST", "/auth/action/confirm", json={"purpose": "verify", "token": token})


def enroll_mfa(actor):
    setup = request(actor, "POST", "/account/mfa/setup", json={"password": PASSWORD})
    code = totp(setup["secret"], int(time.time() // 30))
    return request(actor, "POST", "/account/mfa/confirm", json={"code": code})["recovery_codes"][0]


def test_local_journey_connects_all_roles_with_sessions_and_mfa(browser):
    with TestClient(browser.app) as company, TestClient(browser.app) as admin:
        candidate, _ = register(browser, "acceptance-candidate", skills=["python"], profession="Desarrollador Python")
        employer, _ = register(company, "acceptance-employer", "company", company_name="Laboratorio ficticio", nit="LOCAL-ACCEPTANCE-01")
        staff, _ = register(admin, "acceptance-staff")
        # Staff is provisioned only inside this isolated test; public registration cannot elevate roles.
        with browser.session_factory() as db:
            db.get(User, staff["id"]).role = UserRole.ADMIN
            db.commit()
        sign_in(browser, candidate["email"])
        confirm_mail(browser, candidate["email"])
        assert sign_in(company, employer["email"])["mfa_setup_required"]
        request(company, "GET", "/companies/me", expected=403)
        enroll_mfa(company)
        confirm_mail(company, employer["email"])
        sign_in(admin, staff["email"], admin=True)
        request(admin, "GET", "/admin/stats", expected=403)
        recovery = enroll_mfa(admin)
        request(browser, "GET", "/admin/stats", expected=403)
        # A real HttpOnly session, rather than the legacy bearer helper used in most unit tests.
        assert browser.cookies.get("talentsync_session")
        assert browser.put("/api/v1/account/privacy", json={"share_evidence": False}).status_code == 403
        request(browser, "PUT", "/account/privacy", json={"share_evidence": True, "notify_new_skills": True, "personalize_recommendations": True})

        job = request(company, "POST", "/jobs", expected=201, json={"title": "Desarrollador Python", "description": "Construye APIs con Python y consultas SQL", "requirements": "Fundamentos de Python y SQL", "sector": "Tecnologia y software"})
        assert job["status"] == "draft" and job["blind_hiring"]
        assert request(browser, "GET", "/jobs") == []
        request(company, "POST", "/organization/verification", json={"legal_name": "Laboratorio ficticio", "registry_reference": "Registro sintético LOCAL-001", "representative_role": "Directora"})
        queue = request(admin, "GET", "/admin/verifications")
        assert queue[0]["status"] == "reviewing"
        request(admin, "POST", f"/admin/verifications/{job['company_id']}", json={"status": "verified", "feedback": "Revisión ficticia para la prueba local."})
        request(company, "PATCH", f"/jobs/{job['id']}", json={"status": "active", "skill_requirements": [{"skill": "python", "weight": 2, "essential": True}, {"skill": "sql", "weight": 1, "essential": True}]})
        assert len(request(browser, "GET", "/jobs")) == 1
        request(browser, "PUT", "/personalization/feedback", json={"job_id": job["id"], "interested": True})
        opportunity = request(browser, "GET", f"/learning/jobs/{job['id']}")
        assert [row["key"] for row in opportunity["gaps"]] == ["sql"]
        request(browser, "PUT", "/learning/plans/project-sql", json={"status": "completed"})
        assert "sql" not in request(browser, "GET", "/profiles/me")["skills"]

        application = request(browser, "POST", "/applications", expected=201, json={"job_id": job["id"]})
        ranking = request(company, "GET", f"/recommendations/jobs/{job['id']}/candidates")
        assert ranking[0]["identity_hidden"] and candidate["name"] not in str(ranking)
        request(company, "GET", f"/profiles/candidates/{candidate['id']}", expected=403)
        attempt = request(browser, "POST", "/learning/practical/sql-paid-totals-v1/start")
        practical = f"/learning/practical/attempts/{attempt['id']}"
        assert request(browser, "POST", practical + "/preview", json={"query": SQL})["ok"]
        assert request(browser, "POST", practical + "/submit", json={"query": SQL})["passed"]
        assert request(browser, "GET", "/learning/passport")["assessments"][0]["valid"]
        assert "sql" in request(browser, "GET", "/profiles/me")["skills"]
        assert any(row["type"] == "candidate_skill_validated" for row in request(company, "GET", "/notifications"))
        updated = request(company, "PUT", f"/applications/{application['id']}/status", json={"status": "technical_interview", "expected_version": application["version"], "candidate_feedback": {"reason_code": "other", "message": "Revisamos tus fundamentos; sigamos con la entrevista."}, "recruiter_notes": "PRIVATE-RECRUITER-NOTE"})
        assert not request(company, "GET", f"/recommendations/jobs/{job['id']}/candidates")[0]["identity_hidden"]
        request(company, "GET", f"/profiles/candidates/{candidate['id']}")
        timeline = request(browser, "GET", f"/workflow/applications/{application['id']}")
        assert "PRIVATE-RECRUITER-NOTE" not in str(timeline)
        assert timeline["feedback"]["source"] == "company" and timeline["version"] == updated["version"]

        room = request(company, "POST", "/interviews/rooms", expected=201, json={"application_id": application["id"]})
        endpoint = f"/interviews/rooms/{room['id']}"
        document = {"expected_version": room["version"], "code": "# FICTITIOUS-SHARED-CODE", "whiteboard": [{"points": [{"x": 10, "y": 20}]}]}
        request(browser, "PUT", endpoint, json=document)
        assert request(company, "GET", endpoint)["code"] == document["code"]
        request(company, "PUT", endpoint, expected=409, json=document)
        request(company, "POST", endpoint + "/close")
        assert not request(browser, "GET", endpoint)["active"]

        # The worker endpoint also closes a real overdue process and emits its public feedback exactly once.
        with browser.session_factory() as db:
            db.get(Application, application["id"]).response_due_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
        assert request(admin, "POST", "/admin/workflow/run")["released"] == 1
        assert request(admin, "POST", "/admin/workflow/run")["released"] == 0
        final = request(browser, "GET", f"/workflow/applications/{application['id']}")
        assert final["released_at"] and final["feedback"]["reason_code"] == "response_deadline"
        trust = request(browser, "GET", f"/trust/companies/{job['company_id']}")
        assert trust["missed_deadlines"] == 1
        report = request(browser, "POST", "/trust/incidents", json={"application_id": application["id"], "category": "ghosting", "details": "FICTITIOUS-PRIVATE-DETAILS: proceso de prueba sin respuesta."})
        organization_report = request(company, "GET", "/trust/organization/incidents")[0]
        assert "FICTITIOUS-PRIVATE-DETAILS" not in str(organization_report)
        request(admin, "PATCH", f"/admin/incidents/{report['id']}", json={"status": "dismissed", "shared_summary": "Incidencia ficticia cerrada después de la revisión local."})
        request(admin, "POST", "/admin/ecosystem/audit")
        request(admin, "GET", "/admin/ecosystem")
        request(admin, "GET", "/admin/models")
        request(browser, "PUT", "/account/privacy", json={"share_evidence": False, "notify_new_skills": False, "personalize_recommendations": False})
        assert request(browser, "GET", "/personalization/feedback") == []

        for actor in (browser, company, admin):
            request(actor, "POST", "/auth/session/logout")
            request(actor, "GET", "/auth/me", expected=401)
        assert sign_in(admin, staff["email"], admin=True)["mfa_required"]
        sign_in(admin, staff["email"], admin=True, code=recovery)
        request(admin, "GET", "/admin/stats")
        with browser.session_factory() as db:
            details = str([row.details for row in db.query(EventLog).all()])
            assert PASSWORD not in details and SQL not in details and recovery not in details
            assert "FICTITIOUS-SHARED-CODE" not in details and "FICTITIOUS-PRIVATE-DETAILS" not in details
