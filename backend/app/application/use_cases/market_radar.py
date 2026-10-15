from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.career_coach import owner_profile
from app.application.use_cases.learning_resources import resources
from app.domain.services.experience_dates import experience_months
from app.domain.services.market_radar import families_for, market_report
from app.domain.services.personalization import synthetic_email
from app.domain.services.skills import normalize_skills


def report(db, user, filters, *, local_fixture_mode=False):
    now = datetime.utcnow()
    profile = owner_profile(user)
    families = sorted(families_for(profile.profession or profile.education or ""))
    months = experience_months(profile.experiences)
    suggestion = {"family": next(iter(families), ""),
                  "level": "entry" if months < 12 else "junior" if months < 36 else "mid" if months < 60 else "senior",
                  "location": profile.location or ""}
    if filters.pop("personalized", False):
        filters = {**filters, **suggestion}
    demo = filters.get("dataset") == "demo"
    filters = {**filters, "allow_local_fixtures": local_fixture_mode}
    result = market_report(owner_profile(user), db.jobs.market_jobs(now - timedelta(days=90), demo=demo),
                           db.profiles.market_participants(filters["family"], filters["level"], demo=demo), resources(db), filters, now)
    result["demo_available"] = bool(db.jobs.market_jobs(now - timedelta(days=90), demo=True)) if not demo else True
    result["email_verified"] = user.email_verified
    result["suggested_filters"] = suggestion
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
