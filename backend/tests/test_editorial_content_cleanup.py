# ruff: noqa: F401, F811
import csv
import io
from datetime import datetime, timedelta

from external_fixtures import clear_description
from test_admin_publication_review import admin, external
from test_api_flows import client, create_job, register

from app.infrastructure.database.models import ExternalJobExclusion, Job


def source_import(client, headers, *, description=None):
    row = {"fuente": "greenhouse", "id_externo": "123", "empresa": "Equipo de revisión", "cargo": "Analista de datos",
           "descripcion": description or clear_description("Versión actualizada de la fuente. Revisar información y preparar reportes."),
           "requisitos": "Profesional en Administración. Experiencia mínima de un año. SQL, Excel y Python.",
           "sector": "Tecnologia y software", "enlace_externo": "https://job-boards.greenhouse.io/example/jobs/123",
           "fecha_publicacion": (datetime.utcnow() - timedelta(days=1)).date().isoformat(), "habilidades": "python|sql|excel"}
    buffer = io.StringIO(); writer = csv.DictWriter(buffer, fieldnames=list(row)); writer.writeheader(); writer.writerow(row)
    return client.post("/api/v1/admin/jobs/import", headers=headers, files={"file": ("jobs.csv", buffer.getvalue().encode(), "text/csv")})


def test_external_content_is_versioned_retains_source_and_survives_real_import(client):
    headers = admin(client)
    job_id, _ = external(client)
    endpoint = f"/api/v1/admin/jobs/{job_id}/content"
    detail = client.get(f"/api/v1/admin/jobs/{job_id}/review", headers=headers).json()
    payload = {"revision": 0, "source_url": detail["external_url"], "note": "Transcripción contrastada en las funciones de la oferta original.",
               "fields": {"description": clear_description("Funciones ampliadas por la revisión editorial. Preparar reportes y analizar los registros."),
                          "requirements": "Profesional en Administración. Experiencia mínima de 1 año. Manejo de SQL, Python y Excel.", "salary": 3500000}}
    response = client.patch(endpoint, headers=headers, json=payload)
    assert response.status_code == 200, response.text
    edited = response.json()
    assert edited["moderation_revision"] == 1 and edited["salary"] == 3500000
    assert edited["editorial_overrides"]["source"]["description"] == detail["description"]
    assert edited["external_published_at"] == detail["external_published_at"]
    assert edited["external_checked_at"] == detail["external_checked_at"]
    assert client.patch(endpoint, headers=headers, json=payload).status_code == 409
    response = source_import(client, headers)
    assert response.status_code == 200, response.text
    reloaded = client.get(f"/api/v1/admin/jobs/{job_id}/review", headers=headers).json()
    assert reloaded["description"] == edited["description"] and reloaded["salary"] == 3500000
    assert "Versión actualizada" in reloaded["editorial_overrides"]["source"]["description"]
    assert reloaded["moderation_revision"] == 1


def test_content_cannot_change_source_identity_freshness_or_permissions(client):
    headers = admin(client)
    job_id, _ = external(client)
    payload = {"revision": 0, "source_url": "https://job-boards.greenhouse.io/example/jobs/123", "note": "Revisado en la oferta original.", "fields": {"salary": 2000000}}
    endpoint = f"/api/v1/admin/jobs/{job_id}/content"
    _, candidate = register(client, "reader-content")
    assert client.patch(endpoint, headers=candidate, json=payload).status_code == 403
    assert client.patch(endpoint, headers=headers, json={**payload, "source_url": "https://example.com/another-job"}).status_code == 422
    assert client.patch(endpoint, headers=headers, json={**payload, "fields": {"external_verified_at": datetime.utcnow().isoformat()}}).status_code == 422
    with client.session_factory() as db:
        db.get(Job, job_id).external_check_state = "unknown"; db.commit()
    response = client.patch(endpoint, headers=headers, json=payload)
    assert response.status_code == 200 and not response.json()["external_available"]
    assert not response.json()["review"]["can_publish"]


def test_complete_external_conditions_can_be_edited_again_and_survive_import(client):
    headers = admin(client)
    job_id, _ = external(client)
    endpoint = f"/api/v1/admin/jobs/{job_id}/content"
    initial = client.get(f"/api/v1/admin/jobs/{job_id}/review", headers=headers).json()
    fields = {"title": "Analista de datos y reportes", "description": "Preparar reportes de seguimiento y contrastar los registros del equipo. Documentar diferencias y comunicar resultados.",
              "requirements": "Manejo de SQL, Python y Excel para revisar registros y preparar reportes del equipo.",
              "salary": 3200000, "modality": "hybrid", "employment_type": "full_time", "location": "Medellín", "department": "Antioquia",
              "languages": [{"name": "English", "level": "B2"}], "benefits": ["Formación"],
              "required_education_level": "technical", "required_study_fields": ["Sistemas"],
              "skill_requirements": [{"skill": "SQL", "essential": True, "level": "intermediate", "weight": 3}, {"skill": "python"}, {"skill": "excel"}],
              "quality_details": {"experience_months": 18, "contract_type": "indefinite", "salary_max": 3800000,
                  "work_schedule": {"mode": "fixed", "days": ["mon", "tue", "wed", "thu", "fri"], "start": "08:00", "end": "17:00", "break_minutes": 60},
                  "schedule": "Lunes a viernes de 8:00 a 17:00", "education_accepts_in_progress": True}}
    response = client.patch(endpoint, headers=headers, json={"revision": 0, "source_url": initial["external_url"], "note": "Datos contrastados en los requisitos y condiciones originales.", "fields": fields})
    assert response.status_code == 200, response.text
    edited = response.json()
    assert edited["review"]["can_publish"]
    assert edited["languages"] == [{"name": "inglés", "level": "B2"}]
    assert edited["quality_details"]["weekly_hours"] == 40
    assert edited["quality_details"]["experience_months"] == 18
    assert edited["skill_requirements"][0]["essential"]
    assert edited["external_checked_at"] == initial["external_checked_at"]
    # A second partial save must preserve every other condition and its version.
    response = client.patch(endpoint, headers=headers, json={"revision": 1, "source_url": initial["external_url"], "note": "Se corrigió la experiencia mínima en la misma fuente.", "fields": {"quality_details": {"experience_months": 0}, "languages": []}})
    assert response.status_code == 200, response.text
    assert response.json()["quality_details"]["experience_months"] == 0
    assert response.json()["quality_details"]["contract_type"] == "indefinite"
    assert source_import(client, headers).status_code == 200
    final = client.get(f"/api/v1/admin/jobs/{job_id}/review", headers=headers).json()
    assert final["modality"] == "hybrid" and final["salary"] == 3200000 and final["languages"] == []
    assert final["quality_details"]["experience_months"] == 0 and final["quality_details"]["weekly_hours"] == 40
    assert final["skill_requirements"][0]["essential"] and final["review"]["can_publish"]
    legacy = client.patch(endpoint, headers=headers, json={"revision": 2, "source_url": initial["external_url"], "note": "Se corrigieron las habilidades desde la misma oferta original.", "fields": {"skills": ["SQL", "python", "javascript"]}})
    assert legacy.status_code == 200, legacy.text
    assert legacy.json()["skills"] == ["sql", "python", "javascript"]
    assert legacy.json()["skill_requirements"][0]["essential"]


def test_external_draft_pause_publish_close_and_reopen_are_versioned_and_persist(client):
    headers = admin(client)
    job_id, _ = external(client)
    endpoint = f"/api/v1/admin/jobs/{job_id}/catalog-status"
    for revision, state in enumerate(["draft", "active", "paused", "active", "closed", "active"]):
        response = client.patch(endpoint, headers=headers, json={"revision": revision, "status": state, "note": "Estado decidido después de revisar la oferta original."})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == state and response.json()["moderation_revision"] == revision + 1
        if state != "active":
            assert client.get(f"/api/v1/jobs/{job_id}").status_code == 404
        assert response.json()["editorial_overrides"]["catalog_status"] == state
    assert client.patch(endpoint, headers=headers, json={"revision": 0, "status": "draft", "note": "Revisión anterior"}).status_code == 409
    response = client.patch(endpoint, headers=headers, json={"revision": 6, "status": "paused", "note": "Pausa editorial para revisar condiciones."})
    assert response.status_code == 200
    assert source_import(client, headers).status_code == 200
    detail = client.get(f"/api/v1/admin/jobs/{job_id}/review", headers=headers).json()
    assert detail["status"] == "paused" and detail["moderation_status"] == "held"


def test_publication_still_requires_real_source_evidence_and_partial_invalid_edits_roll_back(client):
    headers = admin(client)
    job_id, _ = external(client)
    with client.session_factory() as db:
        row = db.get(Job, job_id); row.external_check_state = "closed"; db.commit()
    response = client.patch(f"/api/v1/admin/jobs/{job_id}/catalog-status", headers=headers, json={"revision": 0, "status": "active", "note": "No debe saltarse la comprobación de la fuente."})
    assert response.status_code == 422
    endpoint = f"/api/v1/admin/jobs/{job_id}/content"
    payload = {"revision": 0, "source_url": "https://job-boards.greenhouse.io/example/jobs/123", "note": "Contrastado en las condiciones de la oferta."}
    response = client.patch(endpoint, headers=headers, json={**payload, "fields": {"salary": 4000000, "quality_details": {"salary_max": 3000000}}})
    assert response.status_code == 422
    detail = client.get(f"/api/v1/admin/jobs/{job_id}/review", headers=headers).json()
    assert detail["moderation_revision"] == 0
    assert client.patch(endpoint, headers=headers, json={**payload, "fields": {"languages": [{"name": "inglés", "level": "B2"}, {"name": "English", "level": "C1"}]}}).status_code == 422
    assert client.patch(endpoint, headers=headers, json={**payload, "fields": {"external_published_at": (datetime.utcnow() + timedelta(days=3)).isoformat()}}).status_code == 422


def test_original_dates_and_explicit_unknown_conditions_persist_without_forging_a_check(client):
    headers = admin(client)
    job_id, _ = external(client)
    detail_url = f"/api/v1/admin/jobs/{job_id}/review"
    initial = client.get(detail_url, headers=headers).json()
    published = (datetime.utcnow() - timedelta(days=3)).isoformat()
    response = client.patch(f"/api/v1/admin/jobs/{job_id}/content", headers=headers, json={"revision": 0, "source_url": initial["external_url"], "note": "Fechas originales y requisitos transcritos de la fuente.", "fields": {"external_published_at": published, "quality_details": {"experience_months": None, "schedule": "", "work_schedule": None, "weekly_hours": None}}})
    assert response.status_code == 200, response.text
    assert source_import(client, headers).status_code == 200
    final = client.get(detail_url, headers=headers).json()
    assert final["external_published_at"].startswith(published) and final["expires_at"] == initial["expires_at"]
    assert final["quality_details"]["experience_months"] is None
    assert final["quality_details"]["experience_years"] is None
    assert final["external_checked_at"] == initial["external_checked_at"]
    assert final["editorial_overrides"]["source"]["external_published_at"] != final["external_published_at"]


def test_short_incomplete_text_saves_without_becoming_publishable_and_can_be_completed(client):
    headers = admin(client)
    job_id, _ = external(client)
    endpoint = f"/api/v1/admin/jobs/{job_id}/content"
    payload = {"source_url": "https://job-boards.greenhouse.io/example/jobs/123", "note": "Transcripción parcial que se continuará completando."}
    response = client.patch(endpoint, headers=headers, json={**payload, "revision": 0, "fields": {"description": "Preparar reportes", "requirements": "SQL"}})
    assert response.status_code == 200 and not response.json()["review"]["can_activate"]
    response = client.patch(endpoint, headers=headers, json={**payload, "revision": 1, "fields": {"description": "Preparar reportes semanales y contrastar los registros del equipo. Documentar diferencias y comunicar resultados.", "requirements": "Manejo de SQL, Python y Excel para contrastar los registros y preparar los reportes del equipo."}})
    assert response.status_code == 200 and response.json()["review"]["can_activate"]


def test_cleanup_protects_useful_and_temporarily_unavailable_records_and_prevents_reimport(client):
    headers = admin(client)
    old_id, company = external(client)
    native = create_job(client, company)
    temporary = create_job(client, company)
    with client.session_factory() as db:
        old = db.get(Job, old_id); old.external_published_at = datetime.utcnow() - timedelta(days=150)
        transient = db.get(Job, temporary["id"]); transient.source_kind = "external"; transient.external_url = "https://example.com/jobs/temporarily-unavailable"
        transient.external_published_at = datetime.utcnow() - timedelta(days=1); transient.external_check_state = "unavailable"
        db.commit()
    preview = client.get("/api/v1/admin/jobs/cleanup", headers=headers).json()
    assert [row["id"] for row in preview["items"]] == [old_id]
    response = client.post("/api/v1/admin/jobs/cleanup", headers=headers, json={"ids": [old_id, native["id"], temporary["id"]]})
    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 1 and len(response.json()["skipped"]) == 2
    with client.session_factory() as db:
        assert db.get(Job, old_id) is None
        assert db.query(ExternalJobExclusion).one().reason == "old_publication"
        assert db.get(Job, native["id"]) and db.get(Job, temporary["id"])
    response = source_import(client, headers)
    assert response.status_code == 422 and "descartada" in response.text
