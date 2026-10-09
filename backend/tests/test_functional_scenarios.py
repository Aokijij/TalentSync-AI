"""Seeded scenarios must remain usable through the same protected product API."""
import json

import pytest
from test_api_flows import client, register  # noqa: F401

from app.api.schemas.learning import ResourceImport
from app.application.errors import UseCaseError
from app.application.use_cases.organizations import authorize_request
from app.domain.services.personalization import synthetic_email
from app.domain.services.reputation import company_health
from app.infrastructure.database.models import (
    Application,
    Company,
    EventLog,
    LearningPlan,
    User,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.nlp.text_processor import text_processor
from app.infrastructure.security.jwt import create_access_token
from app.infrastructure.security.passwords import verify_password
from scripts import seed_scenarios
from scripts.seed_scenarios import seed, write_guide


def test_connected_bundle_is_idempotent_preserves_existing_data_and_exposes_each_role(client, tmp_path):  # noqa: F811
    original, _ = register(client, "preserved-before-scenarios", skills=["excel"])
    with client.session_factory() as db:
        existing = db.get(User, original["id"])
        original_hash = existing.password_hash
        existing.profile.experience = "Conservar mi trayectoria editada."
        db.commit()
        report, created = seed(db, {}, nlp=text_processor)
        db.commit()
        assert created and report["counts"] == {"users": 26, "candidates": 12, "companies": 8, "team_accounts": 5, "admins": 1, "jobs": 26, "applications": 34, "incidents": 5, "resources": 3}
        assert existing.password_hash == original_hash
        assert existing.profile.experience == "Conservar mi trayectoria editada."
        counts = {table: db.query(table).count() for table in [User, Application, LearningPlan, EventLog]}
        users = {row["key"]: db.get(User, row["id"]) for row in report["accounts"]}
        for account in report["accounts"]:
            assert verify_password(account["password"], users[account["key"]].password_hash)
            assert synthetic_email(account["email"])
        users["senior"].profile.experience = "Edición posterior que no debe reiniciarse."
        db.commit()
        same, created = seed(db, report, nlp=text_processor)
        assert same == report and not created
        assert {table: db.query(table).count() for table in counts} == counts
        assert users["senior"].profile.experience == "Edición posterior que no debe reiniciarse."
        assert company_health(db.get(Company, report["companies"]["empresa"]))["score"] == 100
        assert company_health(db.get(Company, report["companies"]["riesgo"]))["visibility_reduced"]
        assert company_health(db.get(Company, report["companies"]["vacia"]))["score"] is None
        assert {row.status.value for row in users["historial"].applications} == {"submitted", "seen", "reviewing", "shortlisted", "technical_interview", "psychometric_test", "accepted", "hired", "rejected"}
        with pytest.raises(ValueError, match="archivo privado"):
            seed(db, {}, nlp=text_processor)
        uow = SqlAlchemyUnitOfWork(db)
        authorize_request(uow, users["reclutador"], "/api/v1/applications", "GET")
        for key, path in [("entrevistador", "/api/v1/jobs"), ("revocado", "/api/v1/jobs"), ("suspendida", "/api/v1/applications")]:
            with pytest.raises(UseCaseError):
                authorize_request(uow, users[key], path, "GET")

    accounts = {row["key"]: row for row in report["accounts"]}

    def headers(key):
        account = accounts[key]
        return {"Authorization": "Bearer " + create_access_token(str(account["id"]), account["role"])}

    for key, paths in {
        "senior": ["/profiles/me", "/matching/evidence", "/matching/preferences", "/personalization/feedback", "/applications/me", "/notifications"],
        "aprendizaje": ["/learning/catalog?area=all", "/learning/plans", "/learning/passport"],
        "historial": ["/applications/me", "/trust/incidents/me", "/learning/patterns"],
        "empresa": ["/organization/me", "/organization/team", "/organization/invitations", f"/applications/jobs/{report['jobs']['backend']}", "/jobs", "/trust/organization/incidents"],
        "admin": ["/admin/ecosystem", "/admin/incidents", "/admin/learning/resources"],
    }.items():
        for path in paths:
            result = client.get("/api/v1" + path, headers=headers(key))
            assert result.status_code == 200, (key, path, result.text)
    passport = client.get("/api/v1/learning/passport", headers=headers("aprendizaje")).json()
    assert len(passport["practice_evidence"]) == 1
    assert len(passport["assessments"]) == 4
    assert sum(row["valid"] for row in passport["assessments"]) == 2
    assert any(not row["passed"] for row in passport["assessments"])
    assert any(row["passed"] and not row["valid"] for row in passport["assessments"])
    # A full plan enforces the real limit and an archived plan remains readable.
    full = client.get("/api/v1/learning/plans", headers=headers("plan_lleno")).json()
    assert len(full) == 3 and any(not row["resource"]["active"] for row in full)
    assert client.put("/api/v1/learning/plans/project-git", headers=headers("plan_lleno"), json={"status": "in_progress"}).status_code == 409
    assert client.get("/api/v1/matching/preferences", headers=headers("condiciones")).json()["minimum_salary"] == 6000000
    company_apps = client.get(f"/api/v1/applications/jobs/{report['jobs']['backend']}", headers=headers("empresa")).json()
    assert any(row["identity_hidden"] for row in company_apps)
    assert any(not row["identity_hidden"] for row in company_apps)
    for invitation in report["invitations"]:
        from urllib.parse import parse_qs, urlsplit
        token = parse_qs(urlsplit(invitation["url"]).query)["token"][0]
        result = client.get("/api/v1/organization/invitation", params={"token": token}, headers=headers(invitation["key"]))
        assert result.status_code == (404 if invitation["expired"] else 200)
    write_guide(tmp_path, report)
    assert all(account["email"] in (tmp_path / "GUIA_ESCENARIOS.md").read_text(encoding="utf-8") for account in report["accounts"])
    ResourceImport.model_validate(json.loads((tmp_path / "catalogo-ejemplo.json").read_text(encoding="utf-8")))
    for filename in ["vacantes-ejemplo.csv", "vacantes-ejemplo.xlsx", "vacantes-con-error.csv"]:
        result = client.post("/api/v1/admin/jobs/import", headers=headers("admin"), files={"file": (filename, (tmp_path / filename).read_bytes())})
        assert result.status_code == 200, result.text
        imported = result.json()
        if filename == "vacantes-ejemplo.csv":
            assert imported["created"] == 2 and not imported["errors"]
        elif filename == "vacantes-ejemplo.xlsx":
            assert imported["created"] == 0 and imported["updated"] == 2 and not imported["errors"]
        else:
            assert len(imported["errors"]) == 1


def test_command_rejects_any_non_owned_database_before_opening_files(monkeypatch):
    monkeypatch.setattr(seed_scenarios.settings, "environment", "production")
    monkeypatch.setattr(seed_scenarios.settings, "database_url", "postgresql://not-allowed")
    with pytest.raises(SystemExit, match="SQLite aislada"):
        seed_scenarios.main()
