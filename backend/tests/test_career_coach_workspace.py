# ruff: noqa: F811
from datetime import datetime, timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfReader, PdfWriter
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.services.career_coach import (
    demand_report,
    select_jobs,
    vacancy_projection,
)
from app.infrastructure.database.models import Application, Job

BASE = "/api/v1/profiles/me/coach"
FACTS = {"situation": "Faltaba información", "task": "Necesitábamos consultar registros", "action": "Preparé una herramienta de consulta", "result": "El equipo pudo consultar los registros"}


def candidate(client, name="coach-user", role="Asesora comercial", skills=None):
    user, headers = register(client, name, profession=role, skills=skills or ["excel"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["experiences"] = [{"role": role, "company": "Organización", "description": "Preparaba reportes", "start_date": "2020-01", "end_date": "2022-01"}]
    response = client.put("/api/v1/profiles/me", headers=headers, json=profile)
    assert response.status_code == 200, response.text
    return user, headers


def proposal(client, headers):
    state = client.get(BASE, headers=headers).json()
    result = client.post(BASE + "/writing", headers=headers, json={"experience_index": 0, "source_version": state["source_version"], "facts": FACTS})
    assert result.status_code == 200, result.text
    return result.json()


@pytest.mark.parametrize("role", ["Auxiliar de enfermería", "Asesor comercial", "Analista de datos"])
def test_writing_is_shared_across_professions_and_supports_persisted_undo(client, role):
    _, headers = candidate(client, "generic-coach", role)
    item = proposal(client, headers)
    assert client.get("/api/v1/profiles/me", headers=headers).json()["experiences"][0]["description"] == item["before"]
    applied = client.put(BASE + f"/writing/{item['id']}", headers=headers, json={"action": "apply", "text": item["after"] + " Resultado revisado."})
    assert applied.status_code == 200, applied.text
    assert "Resultado revisado" in client.get("/api/v1/profiles/me", headers=headers).json()["experiences"][0]["description"]
    undone = client.put(BASE + f"/writing/{item['id']}", headers=headers, json={"action": "undo"})
    assert undone.status_code == 200, undone.text
    assert client.get("/api/v1/profiles/me", headers=headers).json()["experiences"][0]["description"] == item["before"]
    assert client.get(BASE, headers=headers).json()["writing"][0]["status"] == "undone"


def test_private_history_and_stale_writing_never_overwrite_another_record(client):
    _, a = candidate(client, "coach-a")
    _, b = candidate(client, "coach-b")
    item = proposal(client, a)
    assert client.put(BASE + f"/writing/{item['id']}", headers=b, json={"action": "apply"}).status_code == 404
    p = client.get("/api/v1/profiles/me", headers=a).json()
    p["experiences"][0]["description"] = "Texto confirmado después"
    client.put("/api/v1/profiles/me", headers=a, json=p).raise_for_status()
    assert client.put(BASE + f"/writing/{item['id']}", headers=a, json={"action": "apply"}).status_code == 409
    assert client.get("/api/v1/profiles/me", headers=a).json()["experiences"][0]["description"] == "Texto confirmado después"
    assert client.get(BASE, headers=b).json()["writing"] == []


def test_undo_preserves_later_edits_and_company_cannot_open_private_coach(client):
    _, headers = candidate(client)
    item = proposal(client, headers)
    client.put(BASE + f"/writing/{item['id']}", headers=headers, json={"action": "apply"}).raise_for_status()
    p = client.get("/api/v1/profiles/me", headers=headers).json()
    p["experiences"][0]["description"] = "Edición posterior"
    client.put("/api/v1/profiles/me", headers=headers, json=p).raise_for_status()
    assert client.put(BASE + f"/writing/{item['id']}", headers=headers, json={"action": "undo"}).status_code == 409
    _, company = company_account(client)
    assert client.get(BASE, headers=company).status_code == 403
    assert client.get(BASE + "/pdf").status_code == 401


def draft(client, headers, job_id):
    response = client.post(BASE + "/drafts", headers=headers, json={"job_id": job_id})
    assert response.status_code == 200, response.text
    row = response.json()
    result = client.put(BASE + f"/drafts/{row['id']}", headers=headers, json={"revision": row["revision"], "intro": row["intro"], "confirmed": True})
    assert result.status_code == 200, result.text
    return result.json()


def test_vacancy_versions_are_owned_separate_and_frozen_when_submitted(client):
    user, headers = candidate(client, skills=["python"])
    _, company = company_account(client)
    job = create_job(client, company)
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    row = draft(client, headers, job["id"])
    assert row["profile"]["profession"] == before["profession"]
    assert row["supported_skills"] == ["python"] and any("sql" in question.lower() for question in row["questions"])
    assert client.get("/api/v1/profiles/me", headers=headers).json()["skills"] == ["python"]
    result = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "coach_draft_id": row["id"]})
    assert result.status_code == 201, result.text
    assert result.json()["coach_draft_id"] == row["id"]
    p = client.get("/api/v1/profiles/me", headers=headers).json(); p["profession"] = "Profesión actualizada"
    client.put("/api/v1/profiles/me", headers=headers, json=p).raise_for_status()
    view = client.get(f"/api/v1/profiles/candidates/{user['id']}", headers=company, params={"job_id": job["id"]}).json()
    assert view["profession"] == before["profession"] and view["experience"] == row["intro"] and view["submitted_version"] == row["id"]
    assert client.get(BASE, headers=headers).json()["submitted"][0]["intro"] == row["intro"]
    assert client.get(BASE + "/export", headers=headers, params={"application_id": result.json()["id"]}).status_code == 200
    _, stranger = candidate(client, "export-stranger")
    assert client.get(BASE + "/export", headers=stranger, params={"application_id": result.json()["id"]}).status_code == 404
    with client.session_factory() as db:
        saved = db.get(Application, result.json()["id"])
        assert saved.coach_snapshot["intro"] == row["intro"]


def test_drafts_reject_unconfirmed_foreign_wrong_job_and_stale_sources(client):
    _, a = candidate(client, "draft-a")
    _, b = candidate(client, "draft-b")
    _, company = company_account(client)
    job = create_job(client, company)
    row = client.post(BASE + "/drafts", headers=a, json={"job_id": job["id"]}).json()
    assert client.post("/api/v1/applications", headers=a, json={"job_id": job["id"], "coach_draft_id": row["id"]}).status_code == 422
    assert client.post("/api/v1/applications", headers=b, json={"job_id": job["id"], "coach_draft_id": row["id"]}).status_code == 404
    confirmed = draft(client, a, job["id"])
    assert client.put(BASE + f"/drafts/{confirmed['id']}", headers=a, json={"revision": 1, "intro": "Cambió", "confirmed": True}).status_code == 409
    other = create_job(client, company)
    assert client.post("/api/v1/applications", headers=a, json={"job_id": other["id"], "coach_draft_id": confirmed["id"]}).status_code == 422
    p = client.get("/api/v1/profiles/me", headers=a).json(); p["skills"].append("sql")
    client.put("/api/v1/profiles/me", headers=a, json=p).raise_for_status()
    assert client.post("/api/v1/applications", headers=a, json={"job_id": job["id"], "coach_draft_id": confirmed["id"]}).status_code == 409


def test_blind_selection_does_not_leak_snapshot_description_or_organizations(client):
    user, headers = candidate(client)
    _, company = company_account(client)
    job = create_job(client, company)
    with client.session_factory() as db:
        db.get(Job, job["id"]).blind_hiring = True; db.commit()
    row = draft(client, headers, job["id"])
    client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "coach_draft_id": row["id"]}).raise_for_status()
    view = client.get(f"/api/v1/profiles/candidates/{user['id']}", headers=company, params={"job_id": job["id"]}).json()
    assert view["identity_hidden"] and "Organización" not in str(view) and "Preparaba reportes" not in str(view)
    assert view["cv_guidance"] == {} and view["cv_text"] is None


def test_pdf_original_is_owner_only_and_simple_export_contains_text(client, monkeypatch, tmp_path):
    from app.core.config import settings
    from app.infrastructure.database.models import Profile
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    user, headers = candidate(client)
    other, b = candidate(client, "pdf-other")
    writer = PdfWriter(); writer.add_blank_page(width=595, height=842); output = BytesIO(); writer.write(output)
    path = tmp_path / f"user_{user['id']}_cv.pdf"; path.write_bytes(output.getvalue())
    with client.session_factory() as db:
        p = db.query(Profile).filter_by(user_id=user["id"]).one(); p.cv_filename = "cv.pdf"; p.preferences = {"cv_source_text": "Texto exacto leído\nDos columnas"}; db.commit()
    response = client.get(BASE + "/pdf", headers=headers)
    assert response.status_code == 200 and "no-store" in response.headers["cache-control"]
    assert client.get(BASE + "/pdf", headers=b).status_code == 404
    reading = client.get(BASE + "/reading", headers=headers).json()
    assert reading["text"] == "Texto exacto leído\nDos columnas" and reading["pages"] == 1
    pdf = client.get(BASE + "/export", headers=headers)
    assert pdf.status_code == 200 and "Asesora comercial" in PdfReader(BytesIO(pdf.content)).pages[0].extract_text()
    path.write_bytes(b"<html>not a PDF</html>")
    assert client.get(BASE + "/pdf", headers=headers).status_code == 422


def job(**changes):
    return SimpleNamespace(**{"id": 1, "title": "Asesor comercial", "description": "", "requirements": "", "status": "active", "company_id": 1, "company_name": "Equipo", "sector": "Comercio", "location": "Medellín", "skills": ["excel", "Excel"], "source_name": "TalentSync", "created_at": datetime.utcnow(), "expires_at": None, **changes})


def test_radar_excludes_expired_old_inactive_and_duplicates_and_handles_small_samples():
    items = [job(), job(id=2), job(id=3, status="draft"), job(id=4, expires_at=datetime.utcnow() - timedelta(days=1)), job(id=5, created_at=datetime.utcnow() - timedelta(days=100))]
    profile = SimpleNamespace(skills=[])
    report = demand_report(profile, items, [{"id": "excel", "title": "Excel", "skills": ["excel"], "provider": "SENA"}], search="asesor", location="medellin")
    assert report["sample"] == 1 and report["small_sample"]
    assert report["skills"][0]["count"] == 1 and report["skills"][0]["percentage"] is None and report["skills"][0]["courses"][0]["id"] == "excel"
    assert select_jobs(items, search="enfermería") == []
    big = demand_report(profile, [job(id=i, company_id=i, company_name=str(i)) for i in range(6)], [])
    assert big["sample"] == 6 and big["skills"][0]["percentage"] == 100


def test_adaptation_never_infers_cloud_knowledge_or_changes_formal_titles():
    p = SimpleNamespace(profession="Administrador de servidores", skills=["linux"], experiences=[{"role": "Administrador", "company": "Equipo"}])
    row = vacancy_projection(p, job(title="Ingeniero AWS", skills=["aws", "linux"]))
    assert row["profile"]["profession"] == p.profession and row["supported_skills"] == ["linux"]
    assert "aws" not in row["intro"].lower() and "aws" in row["questions"][0].lower()


def test_generate_from_saved_experience_needs_no_star_form_and_keeps_apply_undo_guards(client):
    _, headers = candidate(client, "generated-coach", "Auxiliar de enfermería")
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["experiences"][0]["description"] = "Atención a pacientes\nApoyo en la elaboración de registros"
    client.put("/api/v1/profiles/me", headers=headers, json=profile).raise_for_status()
    state = client.get(BASE, headers=headers).json()
    payload = {"experience_index": 0, "source_version": state["source_version"]}
    response = client.post(BASE + "/writing/generate", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    row = response.json()
    assert row["after"] == "Atendí a pacientes. Apoyé en la elaboración de registros."
    assert client.get("/api/v1/profiles/me", headers=headers).json()["experiences"][0]["description"] == row["before"]
    assert client.put(BASE + f"/writing/{row['id']}", headers=headers, json={"action": "apply"}).status_code == 200
    assert client.post(BASE + "/writing/generate", headers=headers, json=payload).status_code == 409
    assert client.put(BASE + f"/writing/{row['id']}", headers=headers, json={"action": "undo"}).status_code == 200
    _, other = candidate(client, "generated-stranger")
    assert client.put(BASE + f"/writing/{row['id']}", headers=other, json={"action": "apply"}).status_code == 404
