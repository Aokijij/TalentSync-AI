import json
import time

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.match_settings import evidence
from app.domain.services.skills import normalize_skills

PURPOSE = "project-preview-v1"


def _owner(user):
    return f"{user.id}:{user.created_at.isoformat()}"


def preview(user, file, inspector, security):
    report = inspector.inspect(file)
    now = int(time.time())
    token = security.encrypt_secret(json.dumps({"purpose": PURPOSE, "owner": _owner(user),
        "issued_at": now, "expires_at": now + 600, "report": report}, ensure_ascii=False))
    return {"report": report, "preview_token": token, "expires_in_seconds": 600}


def save(db, user, payload, security):
    try:
        envelope = json.loads(security.decrypt_secret(payload["preview_token"]))
        now = int(time.time())
        if (envelope["purpose"] != PURPOSE or envelope["owner"] != _owner(user)
                or envelope["expires_at"] <= now or envelope["issued_at"] > now + 60):
            raise ValueError("Invalid preview")
        report = envelope["report"]
        available = {row["skill"] for row in report["signals"]}
    except (ValueError, TypeError, KeyError):
        raise UseCaseError(status_code=422, detail="La vista previa venció, fue alterada o corresponde a otra cuenta. Analiza el ZIP de nuevo.") from None
    if not payload["confirm_ownership"] or not set(payload["skills"]) <= available:
        raise UseCaseError(status_code=422, detail="Confirma tu participación y selecciona únicamente tecnologías detectadas")
    if any(row.get("analysis", {}).get("fingerprint") == report["fingerprint"] for row in user.profile.evidence or []):
        raise UseCaseError(status_code=409, detail="Este archivo ya se guardó en tu portafolio")
    if len(user.profile.evidence or []) >= 50:
        raise UseCaseError(status_code=422, detail="Puedes registrar hasta 50 evidencias")
    if payload["add_to_profile"]:
        user.profile.skills = normalize_skills([*(user.profile.skills or []), *payload["skills"]])
    record_event(db, "profile.project_analyzed", "profile", user.profile.id, actor_user_id=user.id,
                 details={"source": report.get("origin", "local_zip"), "version": report["version"]})
    values = {key: payload[key] for key in ("title", "kind", "description", "url", "skills")}
    if report.get("origin") == "github_public":
        values["url"] = report["repository_url"]
    return evidence(db, user, values, analysis=report)
