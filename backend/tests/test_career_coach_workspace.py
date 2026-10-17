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


def seed_historical_snapshot(client, headers, job_id, profile):
    response = client.post("/api/v1/applications", headers=headers, json={"job_id": job_id})
    assert response.status_code == 201, response.text
    with client.session_factory() as db:
        row = db.get(Application, response.json()["id"])
        row.coach_snapshot = {"draft_id": "historical", "intro": "Presentación enviada antes de retirar la función", "profile": profile}
        db.commit()
    return response.json()["id"]


def test_preparation_is_retired_and_advice_is_read_only_owned_and_specific(client):
    _, headers = candidate(client, skills=["python"])
    _, company = company_account(client)
    job = create_job(client, company)
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    assert client.post(BASE + "/drafts", headers=headers, json={"job_id": job["id"]}).status_code == 410
    assert client.put(BASE + "/drafts/old", headers=headers, json={}).status_code == 410
    assert client.get(BASE + "/export", headers=headers, params={"draft_id": "old"}).status_code == 410
    assert client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "coach_draft_id": "x" * 32}).status_code == 422
    advice = client.get(BASE + f"/jobs/{job['id']}/advice", headers=headers)
    assert advice.status_code == 200, advice.text
    assert "python" in str(advice.json()).lower() and "sql" in str(advice.json()).lower()
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before
    assert client.get("/api/v1/applications/me", headers=headers).json() == []
    assert "drafts" not in client.get(BASE, headers=headers).json()
    assert client.get(BASE + f"/jobs/{job['id']}/advice", headers=company).status_code == 403
    assert client.get(BASE + f"/jobs/{job['id']}/advice").status_code == 401
    assert client.get(BASE + "/jobs/999999/advice", headers=headers).status_code == 404


def test_historical_submissions_are_preserved_and_visible_after_submission(client):
    user, headers = candidate(client, skills=["python"])
    _, company = company_account(client)
    job = create_job(client, company)
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    app_id = seed_historical_snapshot(client, headers, job["id"], before)
    updated = {**before, "profession": "Profesión actualizada"}
    client.put("/api/v1/profiles/me", headers=headers, json=updated).raise_for_status()
    endpoint = f"/api/v1/profiles/candidates/{user['id']}"
    view = client.get(endpoint, headers=company, params={"job_id": job["id"]}).json()
    assert view["profession"] == before["profession"] and view["submitted_version"] == "historical"
    with client.session_factory() as db:
        assert db.get(Application, app_id).coach_snapshot["profile"]["profession"] == before["profession"]
        db.get(Job, job["id"]).blind_hiring = True
        db.commit()
    view = client.get(endpoint, headers=company, params={"job_id": job["id"]}).json()
    assert not view["identity_hidden"] and "Organización" in str(view) and "Preparaba reportes" in str(view)
    assert view["profession"] == before["profession"]


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
    pdf = client.get("/api/v1/profiles/me/export", headers=headers)
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


def test_generate_from_saved_experience_needs_no_star_form_and_keeps_apply_undo_guards(client):
    from app.api.deps import get_career_writer
    class Writer:
        def generate(self, record, *, style, result):
            return {"text": "Mi trabajo se centró en atender pacientes y apoyar la elaboración de registros.", "idea": "¿Qué registro entregabas al equipo?"}
    client.app.dependency_overrides[get_career_writer] = lambda: Writer()
    _, headers = candidate(client, "generated-coach", "Auxiliar de enfermería")
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile["experiences"][0]["description"] = "Atención a pacientes\nApoyo en la elaboración de registros"
    client.put("/api/v1/profiles/me", headers=headers, json=profile).raise_for_status()
    state = client.get(BASE, headers=headers).json()
    payload = {"experience_index": 0, "source_version": state["source_version"]}
    response = client.post(BASE + "/writing/generate", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    row = response.json()
    assert row["after"] == "Mi trabajo se centró en atender pacientes y apoyar la elaboración de registros."
    assert row["method"] == "local-ai" and row["questions"]
    assert client.get("/api/v1/profiles/me", headers=headers).json()["experiences"][0]["description"] == row["before"]
    assert client.put(BASE + f"/writing/{row['id']}", headers=headers, json={"action": "apply"}).status_code == 200
    assert client.post(BASE + "/writing/generate", headers=headers, json=payload).status_code == 409
    assert client.put(BASE + f"/writing/{row['id']}", headers=headers, json={"action": "undo"}).status_code == 200
    _, other = candidate(client, "generated-stranger")
    assert client.put(BASE + f"/writing/{row['id']}", headers=other, json={"action": "apply"}).status_code == 404
