from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.career_coach import owner_profile
from app.application.use_cases.learning_resources import resources
from app.domain.services.market_radar import market_report
from app.domain.services.personalization import synthetic_email
from app.domain.services.skills import normalize_skills


def report(db, user, filters):
    now = datetime.utcnow()
    result = market_report(owner_profile(user), db.jobs.market_jobs(now - timedelta(days=90)),
                           db.profiles.market_participants(filters["family"], filters["level"]), resources(db), filters, now)
    result["email_verified"] = user.email_verified
    return result


def participate(db, user, payload):
    profile = owner_profile(user)
    if payload["enabled"] and (synthetic_email(user.email) or user.email.lower().endswith((".invalid", ".localhost"))):
        raise UseCaseError(status_code=422, detail="Las cuentas de demostración o prueba no participan en estadísticas reales")
    if payload["enabled"] and not profile.location:
        raise UseCaseError(status_code=422, detail="Completa primero tu ciudad en Mi perfil")
    db.profiles.lock_owner(user.id); db.refresh(profile)
    choice = {"enabled": payload["enabled"], "family": payload["family"], "level": payload["level"],
              "confirmed_real": payload["enabled"] and payload["confirm_real_profile"], "updated_at": datetime.utcnow().isoformat() + "Z"}
    profile.preferences = {**(profile.preferences or {}), "market_participation": choice}
    db.add(profile); db.commit()
    return {"participation": choice, "email_verified": user.email_verified}


def declare_skill(db, user, payload, nlp):
    if not payload["confirm"] or not payload["skill"].strip():
        raise UseCaseError(status_code=422, detail="Confirma que conoces la habilidad antes de añadirla")
    profile = owner_profile(user)
    db.profiles.lock_owner(user.id); db.refresh(profile)
    skills = normalize_skills([*(profile.skills or []), payload["skill"]])
    if len(skills) > 100:
        raise UseCaseError(status_code=422, detail="Tu perfil admite hasta cien habilidades")
    profile.skills = skills
    profile.embedding = nlp.embed(" ".join(filter(None, [profile.profession, profile.experience, " ".join(skills)])))
    db.add(profile); db.commit(); db.refresh(profile)
    return profile
