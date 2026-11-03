"""Explicit admin refreshes; candidates only read stored public metadata."""
import copy
import time
from datetime import datetime, timedelta
from hashlib import sha256

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.services.learning_availability import availability


def cached(db, key, fetch, *, force=False):
    now = datetime.utcnow()
    row = db.learning.source_snapshot(key)
    if row and (now - row.attempted_at < timedelta(minutes=2) or not force and now - row.fetched_at < timedelta(hours=24)):
        return copy.deepcopy(row.content), row
    try:
        content = fetch()
    except UseCaseError:
        if row:
            row.attempted_at, row.error = now, "No se pudo actualizar la fuente oficial; se conserva la última lectura."
            db.commit()
            return copy.deepcopy(row.content), row
        row = db.learning.new_source_snapshot(id=key, content=[], fetched_at=now - timedelta(days=2),
                                             attempted_at=now, error="La primera consulta de la fuente no pudo completarse.")
        db.add(row)
        db.commit()
        raise
    if row is None:
        db.learning.trim_source_snapshots()
        row = db.learning.new_source_snapshot(id=key, content=content)
        db.add(row)
    row.content, row.fetched_at, row.attempted_at, row.error = content, now, now, ""
    db.commit()
    return copy.deepcopy(content), row


def preview_sena(db, user, gateway, query, force=False):
    query = " ".join(query.split())
    if len(query) < 3:
        raise UseCaseError(status_code=422, detail="Escribe al menos tres caracteres para buscar formación.")
    key = "sena-search:" + sha256(query.casefold().encode()).hexdigest()[:32]
    rows, snapshot = cached(db, key, lambda: gateway.search(query), force=force)
    return gateway.preview(rows, user.id, fetched_at=snapshot.fetched_at.isoformat(), warning=snapshot.error,
                           notice="Habilidades sugeridas por palabras del título: revisa la ficha y el temario antes de publicar.")


def opportunities(db):
    row = db.learning.source_snapshot("sapiencia")
    if not row:
        return {"items": [], "fetched_at": None, "warning": "Pendiente de consultar la fuente oficial."}
    items = [{**item, **availability({"details": {"enrollment": item}, "source": {"observation": {"unavailable": bool(row.error)}}})} for item in row.content]
    return {"items": items, "fetched_at": row.fetched_at.isoformat(), "warning": row.error}


def refresh_sapiencia(db, user, gateway, force=False):
    _, snapshot = cached(db, "sapiencia", gateway.opportunities, force=force)
    record_event(db, "learning.sources_refreshed", "catalog", None, actor_user_id=user.id,
                 details={"source": "sapiencia", "status": "retained" if snapshot.error else "checked"})
    db.commit()
    return opportunities(db)


def refresh_sena(db, user, gateway, *, limit=5, force=False, budget_seconds=12):
    rows = [row for row in db.learning.resources() if row.content.get("source", {}).get("provider") == "sena"]
    rows.sort(key=lambda row: row.content.get("source", {}).get("observation", {}).get("checked_on", ""))
    checked, failed = 0, 0
    deadline = time.monotonic() + budget_seconds
    for row in rows:
        observation = row.content.get("source", {}).get("observation", {})
        if not force and observation.get("checked_on") == datetime.utcnow().date().isoformat() and not observation.get("unavailable"):
            continue
        if checked + failed >= limit or time.monotonic() > deadline or failed >= 2:
            break
        # Persisted cache also bounds retries after provider outages.
        key = "sena-course:" + sha256(row.content["url"].encode()).hexdigest()[:32]
        try:
            value, snapshot = cached(db, key, lambda url=row.content["url"]: gateway.observe(url), force=force)
            if snapshot.error:
                failed += 1
                value = {**observation, "unavailable": True, "notes": snapshot.error}
            else:
                checked += 1
        except UseCaseError:
            failed += 1
            value = {**observation, "unavailable": True, "notes": "No se pudo comprobar la inscripción; consulta la ficha oficial."}
            # Do not mark a failed check as a successful check today.
        source = {**row.content["source"], "observation": value}
        row.content = {**row.content, "source": source}
        db.add(row)
        db.commit()
    record_event(db, "learning.sources_refreshed", "catalog", None, actor_user_id=user.id,
                 details={"source": "sena", "status": "partial" if failed else "checked"})
    db.commit()
    return {"checked": checked, "failed": failed, "total": len(rows)}
