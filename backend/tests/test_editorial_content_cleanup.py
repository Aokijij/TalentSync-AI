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
