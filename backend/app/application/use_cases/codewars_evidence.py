import json
import time
from datetime import datetime, timezone

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.match_settings import evidence
from app.domain.services.skills import normalize_skills

PURPOSE = "codewars-preview-v1"


def preview(user, username, reader, security):
    report = reader.inspect(username)
    now = int(time.time())
    token = security.encrypt_secret(json.dumps({"purpose": PURPOSE,
        "owner": f"{user.id}:{user.created_at.isoformat()}", "issued_at": now,
        "expires_at": now + 600, "report": report}, ensure_ascii=False))
    return {"report": report, "preview_token": token, "expires_in_seconds": 600}


def save(db, user, payload, security):
    try:
        envelope = json.loads(security.decrypt_secret(payload["preview_token"]))
        now = int(time.time())
        if (envelope["purpose"] != PURPOSE or envelope["owner"] != f"{user.id}:{user.created_at.isoformat()}"
                or envelope["expires_at"] <= now or envelope["issued_at"] > now + 60):
            raise ValueError("Invalid preview")
        report = envelope["report"]
        available = {row["skill"] for row in report["signals"]}
    except (ValueError, TypeError, KeyError):
        raise UseCaseError(status_code=422, detail="La vista previa venció, fue alterada o pertenece a otra cuenta. Consulta Codewars nuevamente.") from None
    if not payload["confirm_ownership"] or not set(payload["skills"]) <= available:
        raise UseCaseError(status_code=422, detail="Confirma que la cuenta es tuya y elige únicamente lenguajes de la consulta.")
    values = {key: payload[key] for key in ("title", "description", "skills", "add_to_profile")}
    values.update(kind="portfolio", url=report["profile_url"])
    # Refresh a linked account in place rather than accumulating snapshots.
    existing = next((row for row in user.profile.evidence or [] if
        row.get("analysis", {}).get("origin") == "codewars_public" and
        row["analysis"].get("username", "").casefold() == report["username"].casefold()), None)
    if existing:
        if values["add_to_profile"]:
            skills = normalize_skills([*(user.profile.skills or []), *values["skills"]])
            if len(skills) > 100:
                raise UseCaseError(status_code=422, detail="Tu perfil admite hasta cien habilidades.")
            user.profile.skills = skills
        updated = {**existing, **values, "analysis": report, "verified": False,
                   "updated_at": datetime.now(timezone.utc).isoformat()}
        user.profile.evidence = [updated if row["id"] == existing["id"] else row for row in user.profile.evidence]
        user.profile.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        record_event(db, "profile.codewars_updated", "profile", user.profile.id, actor_user_id=user.id)
        db.commit()
        return user.profile.evidence
    return evidence(db, user, values, analysis=report)
