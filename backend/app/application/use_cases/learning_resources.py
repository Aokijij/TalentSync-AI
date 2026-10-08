from datetime import datetime
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.services.learning_catalog import ASSESSMENTS, LOCAL_RESOURCES
from app.domain.services.sql_challenges import CHALLENGES


def enrich(resource):
    return {**resource, "assessment_ids": [key for key, bank in ASSESSMENTS.items() if bank["skill"] in resource["skills"]],
            "practical_ids": [key for key, bank in CHALLENGES.items() if bank["skill"] in resource["skills"]]}


def resources(db, include_inactive=False):
    return [enrich({**row, "active": True, "affiliate": False, "cost": "free"}) for row in LOCAL_RESOURCES] + [
        enrich({**row.content, "id": row.id, "active": row.active, "version": row.version})
        for row in db.learning.resources() if include_inactive or row.active]


def manage(db, user, payloads=None, resource_id=None, version=None):
    if payloads is None:
        return resources(db, include_inactive=True)
    if resource_id:
        row = db.learning.resource(resource_id)
        if row is None:
            raise UseCaseError(status_code=404, detail="Recurso administrable no encontrado")
        if row.version != version:
            raise UseCaseError(status_code=409, detail="El recurso cambió; actualiza antes de guardar")
        targets = [row]
    else:
        if len(db.learning.resources()) + len(payloads) > 200:
            raise UseCaseError(status_code=422, detail="El catálogo admite hasta doscientos recursos administrables")
        targets = [db.learning.new_resource(id=f"course-{uuid4().hex}") for _ in payloads]
    for row, content in zip(targets, payloads, strict=True):
        row.active = content["active"]
        row.content = {key: value for key, value in content.items() if key not in {"active", "version"}}
        row.updated_at = datetime.utcnow()
        db.add(row)
    record_event(db, "learning.catalog_updated", "catalog", None, actor_user_id=user.id,
                 details={"source": "manual", "status": "updated" if resource_id else "created"})
    db.commit()
    return resources(db, include_inactive=True)
