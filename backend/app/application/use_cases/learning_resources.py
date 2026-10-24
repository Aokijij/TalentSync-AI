from datetime import datetime
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.services.learning_availability import availability
from app.domain.services.learning_catalog import ASSESSMENTS, LOCAL_RESOURCES
from app.domain.services.learning_journeys import journey_for
from app.domain.services.skills import skill_key
from app.domain.services.sql_challenges import CHALLENGES


def retired_resource(resource):
    provider = skill_key(resource.get("provider", ""))
    return not resource.get("url") or "fictici" in provider or provider.startswith("talentsync")


def enrich(resource, private=False):
    from app.domain.services.challenge_tracks import (
        course_skills_for,
        related_assessments,
    )
    from app.domain.services.course_practices import public_resource
    resource = {**resource}
    if urlsplit(resource.get("url") or "").hostname in {"www.youtube.com", "youtube.com", "youtu.be"}:
        resource["provider"] = "YouTube"
        resource["title"] = {
            "Primeros reportes administrativos con Excel": "Excel: reportes administrativos en vídeo",
            "Prepara datos de oficina con Power Query": "Power Query: preparación de datos en vídeo",
            "Documentos claros para el trabajo con Word": "Word: documentos de trabajo en vídeo",
            "Python inicial con un proyecto para practicar": "Python: fundamentos y ejercicios en vídeo",
            "Organiza y documenta versiones de un proyecto con Git": "Git: control de versiones en vídeo",
            "Consulta y explica datos relacionales con SQL": "SQL: consultas y bases de datos en vídeo",
        }.get(resource.get("title"), resource.get("title"))
    if retired_resource(resource):
        resource["active"] = False
    assigned = related_assessments(resource, ASSESSMENTS)
    result = {**resource, "retired": retired_resource(resource), "availability": availability(resource), "journey": journey_for(resource) if private or not resource.get("url") else None, "assessment_ids": assigned,
              "assigned_challenges": [{"id": key, "course_skills": course_skills_for(resource, ASSESSMENTS[key]), **{field: ASSESSMENTS[key].get(field) for field in ("title", "skill", "level", "minutes", "question_count", "context")}} for key in assigned],
              "practical_ids": [key for key, bank in CHALLENGES.items() if bank["skill"] in resource["skills"]]}
    return result if private else public_resource(result)


def resources(db, include_inactive=False, private=False):
    managed = db.learning.resources()
    managed_urls = {row.content.get("url", "").rstrip("/") for row in managed
                    if row.content.get("url") and (row.active or row.content.get("_published_once"))}
    # Keep legacy IDs available to existing plans, while preventing their older
    # reference cards from duplicating or reviving an administrable course.
    originals = [enrich({**row, "active": not row.get("url") or row["url"].rstrip("/") not in managed_urls,
                         "affiliate": False, "cost": "free"}, private=private) for row in LOCAL_RESOURCES]
    all_resources = originals + [
        enrich({**{key: value for key, value in row.content.items() if key != "_published_once"},
                "id": row.id, "active": row.active, "version": row.version}, private=private)
        for row in managed]
    return all_resources if include_inactive else [row for row in all_resources if row["active"]]


def manage(db, user, payloads=None, resource_id=None, version=None):
    if payloads is None:
        return resources(db, include_inactive=True, private=True)
    if resource_id:
        row = db.learning.resource(resource_id)
        if row is None:
            raise UseCaseError(status_code=404, detail="Recurso administrable no encontrado")
        if row.version != version:
            raise UseCaseError(status_code=409, detail="El recurso cambió; actualiza antes de guardar")
        targets = [row]
    else:
        if len(db.learning.resources()) + len(payloads) > 1000:
            raise UseCaseError(status_code=422, detail="El catálogo admite hasta mil recursos administrables")
        targets = [db.learning.new_resource(id=f"course-{uuid4().hex}") for _ in payloads]
    for row, content in zip(targets, payloads, strict=True):
        source = row.content.get("source") if resource_id else None
        previous_details = row.content.get("details") if resource_id else None
        previous_practice = row.content.get("practice") if resource_id else None
        published_before = (row.active or row.content.get("_published_once", False)) if resource_id else False
        row.active = content["active"]
        row.content = {key: value for key, value in content.items() if key not in {"active", "version"}}
        if resource_id and source:
            row.content["source"] = source
        if previous_details and content.get("details") is None:
            row.content["details"] = previous_details
        if previous_practice and content.get("practice") is None:
            row.content["practice"] = previous_practice
        if published_before or row.active:
            row.content["_published_once"] = True
        row.updated_at = datetime.utcnow()
        db.add(row)
    record_event(db, "learning.catalog_updated", "catalog", None, actor_user_id=user.id,
                 details={"source": "manual", "status": "updated" if resource_id else "created"})
    db.commit()
    return resources(db, include_inactive=True, private=True)


def import_source(db, user, selected, *, namespace="microsoft_learn", publish=False):
    # Deterministic IDs prevent repeated imports from multiplying a course. Existing
    # editorial changes and published plans are deliberately preserved on reimport.
    prefix = "learn" if namespace == "microsoft_learn" else namespace
    targets = [(f"course-{prefix}-{sha256(item['source_id'].encode()).hexdigest()[:32]}", item) for item in selected]
    existing = db.learning.resources()
    identities = {(row.content.get("source", {}).get("provider"), row.content.get("source", {}).get("id")) for row in existing}
    urls = {row.content.get("url", "").rstrip("/") for row in existing}
    new = []
    for key, item in targets:
        identity = (item["source"].get("provider"), item["source"].get("id"))
        url = item["content"]["url"].rstrip("/")
        if db.learning.resource(key) is None and identity not in identities and url not in urls:
            new.append((key, item))
            identities.add(identity)
            urls.add(url)
    if len(db.learning.resources()) + len(new) > 1000:
        raise UseCaseError(status_code=422, detail="El catálogo admite hasta mil recursos administrables")
    for key, item in new:
        row = db.learning.new_resource(id=key)
        row.active = publish
        row.content = {key: value for key, value in item["content"].items() if key != "active"}
        row.content["source"] = item["source"]
        if publish:
            row.content["_published_once"] = True
        row.updated_at = datetime.utcnow()
        db.add(row)
    record_event(db, "learning.catalog_updated", "catalog", None, actor_user_id=user.id,
                 details={"source": namespace, "status": "imported_active" if publish else "imported_draft"})
    db.commit()
    return {"resources": resources(db, include_inactive=True, private=True), "created": len(new), "existing": len(targets) - len(new)}
