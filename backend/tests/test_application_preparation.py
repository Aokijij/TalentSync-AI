# ruff: noqa: F811
from datetime import datetime, timedelta
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

from pypdf import PdfReader
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.infrastructure.database.models import (
    Application,
    EventLog,
    Job,
    Notification,
    ResumeVersion,
    User,
)

BASE = "/api/v1/profiles/me/coach"


def setup_case(client):
    owner, headers = register(client, "preparation-owner", profession="Analista de datos", skills=["python", "excel"])
    _, company = company_account(client, "preparation-company")
    job = create_job(client, company)
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile.update(experience="Preparaba reportes para el equipo.", experiences=[
        {"role": "Analista de datos", "company": "Equipo de reportes", "description": "Usé Python para preparar reportes.", "start_date": "2020-01", "end_date": "2022-01"},
        {"role": "Auxiliar de inventario", "company": "Bodega", "description": "Controlé el inventario.", "start_date": "2018-01", "end_date": "2019-01"},
    ], certifications=[{"name": "Excel básico", "issuer": "SENA", "year": "2020", "kind": "course"}])
    updated = client.put("/api/v1/profiles/me", headers=headers, json=profile)
    assert updated.status_code == 200, updated.text
    return owner, headers, company, job


def pack(client, headers, job_id):
    response = client.get(f"{BASE}/jobs/{job_id}/preparation", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def create_version(client, headers, job_id, **changes):
    data = pack(client, headers, job_id)
    payload = {"request_key": str(uuid4()), "source_version": data["source_version"], "job_version": data["job_version"], "include_photo": False, **changes}
    response = client.post(f"{BASE}/jobs/{job_id}/cv-versions", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json(), payload


def test_cv_selection_is_private_does_not_change_profile_and_keeps_exact_pdf(client):
    owner, headers, company, job = setup_case(client)
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    version, _ = create_version(client, headers, job["id"], experience_indices=[0], skills=["python"], summary="Mi experiencia relacionada con esta oferta.")
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before
    endpoint = f"{BASE}/cv-versions/{version['id']}/pdf"
    pdf = client.get(endpoint, headers=headers)
    assert pdf.status_code == 200 and "no-store" in pdf.headers["cache-control"]
    assert sha256(pdf.content).hexdigest() == version["sha256"]
    contents = " ".join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
    assert "Mi experiencia relacionada" in contents and "Equipo de reportes" in contents and "SENA" in contents
    assert "Auxiliar de inventario" not in contents and "Bodega" not in contents
    _, stranger = register(client, "preparation-stranger")
    assert client.get(endpoint, headers=stranger).status_code == 404
    assert client.get(endpoint, headers=company).status_code == 403
    assert client.get(endpoint).status_code == 401
    application = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "resume_version_id": version["id"]})
    assert application.status_code == 201, application.text
    application_id = application.json()["id"]
    assert application.json()["resume_version_id"] == version["id"]
    with client.session_factory() as db:
        stored = db.get(User, owner["id"]).profile
        stored.experience = "Ahora mi perfil tiene otro resumen"
        stored.skills = ["otra habilidad"]
        db.get(Job, job["id"]).description = "Oferta actualizada después de postularme"
        db.commit()
    assert client.get(endpoint, headers=headers).content == pdf.content
    assert client.get(f"/api/v1/applications/{application_id}/resume", headers=headers).content == pdf.content
    assert client.get(f"/api/v1/applications/{application_id}/resume", headers=company).content == pdf.content
    assert client.get(f"/api/v1/applications/{application_id}/resume", headers=stranger).status_code == 403
    view = client.get(f"/api/v1/profiles/candidates/{owner['id']}", headers=company, params={"job_id": job["id"]}).json()
    assert view["skills"] == ["python"] and view["experience"] == "Mi experiencia relacionada con esta oferta."
    process_pack = client.get(f"{BASE}/applications/{application_id}/preparation", headers=headers).json()
    assert process_pack["source"] == "submitted" and process_pack["submitted_resume_id"] == version["id"]
    assert "actualizada después" not in process_pack["job"]["description"]


def test_duplicate_requests_and_lost_application_response_do_not_duplicate_effects(client):
    _, headers, company, job = setup_case(client)
    version, payload = create_version(client, headers, job["id"])
    duplicate = client.post(f"{BASE}/jobs/{job['id']}/cv-versions", headers=headers, json=payload)
    assert duplicate.status_code == 201 and duplicate.json()["id"] == version["id"]
    conflict = client.post(f"{BASE}/jobs/{job['id']}/cv-versions", headers=headers, json={**payload, "summary": "Otra versión"})
    assert conflict.status_code == 409
    submitted = {"job_id": job["id"], "resume_version_id": version["id"]}
    first = client.post("/api/v1/applications", headers=headers, json=submitted)
    assert first.status_code == 201
    with client.session_factory() as db:
        db.get(Job, job["id"]).status = "closed"
        db.commit()
    retry = client.post("/api/v1/applications", headers=headers, json=submitted)
    assert retry.status_code == 201 and retry.json()["id"] == first.json()["id"]
    other_tab = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]})
    assert other_tab.status_code == 201 and other_tab.json()["resume_version_id"] == version["id"]
    with client.session_factory() as db:
        assert db.query(ResumeVersion).count() == 1 and db.query(Application).count() == 1
        assert db.query(Notification).filter_by(type="application_received").count() == 1
        assert db.query(EventLog).filter_by(event_type="application.transition").count() == 1


def test_stale_profile_unknown_skills_foreign_versions_and_expired_jobs_are_rejected(client):
    owner, headers, company, job = setup_case(client)
    version, payload = create_version(client, headers, job["id"])
    with client.session_factory() as db:
        db.get(User, owner["id"]).profile.phone = "+57 300 111 2222"
        db.commit()
    stale = client.post(f"{BASE}/jobs/{job['id']}/cv-versions", headers=headers, json={**payload, "request_key": str(uuid4())})
    assert stale.status_code == 409
    current = pack(client, headers, job["id"])["source_version"]
    for changes in [{"skills": ["habilidad inventada"]}, {"experience_indices": [99]}, {"experience_indices": [0, 0]}]:
        response = client.post(f"{BASE}/jobs/{job['id']}/cv-versions", headers=headers, json={**payload, "source_version": current, "request_key": str(uuid4()), **changes})
        assert response.status_code == 422, response.text
    _, other = register(client, "preparation-foreign")
    assert client.post("/api/v1/applications", headers=other, json={"job_id": job["id"], "resume_version_id": version["id"]}).status_code == 404
    another_job = create_job(client, company)
    assert client.post("/api/v1/applications", headers=headers, json={"job_id": another_job["id"], "resume_version_id": version["id"]}).status_code == 422
    assert client.post(f"{BASE}/jobs/{another_job['id']}/cv-versions", headers=headers, json=payload).status_code == 409
    with client.session_factory() as db:
        db.get(Job, job["id"]).expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get(f"{BASE}/jobs/{job['id']}/preparation", headers=headers).status_code == 404


def test_interview_notes_survive_reload_remain_private_and_detect_two_tab_conflicts(client):
    _, headers, company, job = setup_case(client)
    data = pack(client, headers, job["id"])
    assert any(question.get("skill") == "python" for question in data["interview"]["questions"])
    assert any(question.get("skill") == "sql" and not question["in_profile"] for question in data["interview"]["questions"])
    question = data["interview"]["questions"][0]["id"]
    answers = {question: {"situation": "PRIVATE-EXAMPLE", "task": "Preparar un reporte", "action": "Ordené los registros", "result": "El equipo lo pudo consultar"}}
    payload = {"expected_version": 0, "revision": data["revision"], "answers": answers}
    endpoint = f"{BASE}/jobs/{job['id']}/interview"
    response = client.put(endpoint, headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["reviews"][question] == {"complete": True, "missing": []}
    assert client.put(endpoint, headers=headers, json=payload).status_code == 409
    loaded = pack(client, headers, job["id"])
    assert loaded["interview"]["answers"] == answers and loaded["interview"]["version"] == 1
    _, other = register(client, "preparation-notes-other")
    assert pack(client, other, job["id"])["interview"]["answers"] == {}
    assert client.put(endpoint, headers=company, json=payload).status_code == 403
    assert client.get(f"{BASE}/jobs/{job['id']}/preparation", headers=company).status_code == 403
    with client.session_factory() as db:
        db.get(Job, job["id"]).skills = ["logística"]
        db.commit()
    assert pack(client, headers, job["id"])["interview"]["outdated"] is True
    assert client.put(endpoint, headers=headers, json={**payload, "expected_version": 1}).status_code == 409


def test_normal_submission_freezes_facts_and_closed_process_can_still_be_prepared(client):
    owner, headers, company, job = setup_case(client)
    application = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"]}).json()
    with client.session_factory() as db:
        db.get(User, owner["id"]).profile.experience = "Resumen posterior"
        db.get(Job, job["id"]).status = "closed"
        db.commit()
    endpoint = f"{BASE}/applications/{application['id']}/preparation"
    response = client.get(endpoint, headers=headers)
    assert response.status_code == 200 and response.json()["source"] == "submitted"
    question = response.json()["interview"]["questions"][0]
    assert any("reportes" in str(row) for row in question["experiences"])
    payload = {"expected_version": 0, "revision": response.json()["revision"], "answers": {question["id"]: {"action": "Mi respuesta privada"}}}
    saved = client.put(endpoint.replace("/preparation", "/interview"), headers=headers, json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["reviews"][question["id"]]["complete"] is False
    _, other = register(client, "preparation-process-other")
    assert client.get(endpoint, headers=other).status_code == 403
    assert "Mi respuesta privada" not in client.get(f"/api/v1/workflow/applications/{application['id']}", headers=company).text


def test_blind_process_never_exposes_submitted_pdf_through_another_revealed_process(client, monkeypatch):
    owner, headers, company, job = setup_case(client)
    version, _ = create_version(client, headers, job["id"])
    response = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "resume_version_id": version["id"]})
    application_id = response.json()["id"]
    with client.session_factory() as db:
        db.get(Job, job["id"]).blind_hiring = True
        db.get(Application, application_id).identity_revealed_at = None
        db.commit()
    # The identity policy currently reveals a self-submitted application. Exercise
    # the hidden state explicitly so future changes cannot expose this PDF.
    from app.application.use_cases import application_preparation
    monkeypatch.setattr(application_preparation, "identity_hidden", lambda *_: True)
    assert client.get(f"/api/v1/applications/{application_id}/resume", headers=company).status_code == 403
    assert client.get(f"/api/v1/applications/{application_id}/resume", headers=headers).status_code == 200
