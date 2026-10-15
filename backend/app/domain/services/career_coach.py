"""Shared coach operations for any occupation; confirmed data is the source."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta

from app.domain.services.skill_context import fold
from app.domain.services.skills import skill_key, skill_set

PROFILE_FIELDS = ("profession", "skills", "skill_levels", "experience", "education", "location", "department", "phone", "availability", "preferred_modality", "preferred_sector", "desired_salary", "experiences", "educations", "certifications", "languages")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def snapshot(profile):
    return json.loads(json.dumps({key: getattr(profile, key, None) for key in PROFILE_FIELDS}, default=str))


def star_text(facts):
    values = [str(facts.get(key, "")).strip() for key in ("situation", "task", "action", "result")]
    if any(not value or re.search(r"\[[^\]]+\]", value) for value in values):
        raise ValueError("Completa los cuatro hechos con tus datos reales, sin marcadores pendientes")
    return " ".join(value if value[-1] in ".!?" else value + "." for value in values)


def document_review(profile, text):
    """Explain concrete import checks without rating a candidate or an ATS."""
    source = re.sub(r"\s+", " ", fold(text))
    def present(value):
        needle = re.sub(r"\s+", " ", fold(value)).strip()
        return bool(needle) and needle in source
    experiences = profile.experiences or []
    studies = profile.educations or []
    matched_jobs = sum(present(item.get("role")) and present(item.get("company")) for item in experiences)
    matched_studies = sum(present(item.get("degree")) and present(item.get("institution")) for item in studies)
    skills = [skill for skill in profile.skills or [] if re.search(r"(?<!\w)" + re.escape(fold(skill)) + r"(?!\w)", source)]
    possible_phones = re.findall(r"(?<!\d)(?:\+?\d[\d ()-]{6,}\d)(?!\d)", fold(text))
    phone = any(7 <= len(re.sub(r"\D", "", value)) <= 15 and not re.search(r"(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}", value) for value in possible_phones)
    contact = bool(re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", source)) and phone
    return [
        {"title": "Datos de contacto", "ok": contact, "detail": "Encontramos un correo y un posible teléfono. Comprueba que sean los que quieres compartir." if contact else "No encontramos un correo y un teléfono claros. Revisa tus datos de contacto.", "target": "profile-contact", "action": "Revisar contacto"},
        {"title": "Experiencia laboral", "ok": bool(experiences) and matched_jobs == len(experiences), "detail": f"Coinciden cargo y empresa en {matched_jobs} de {len(experiences)} experiencias del perfil. Comprueba también las fechas." if experiences else "No hay experiencias guardadas para comparar. Puedes añadir empleos, prácticas o mostrar proyectos en tus evidencias.", "target": "profile-experiences", "action": "Revisar experiencia"},
        {"title": "Formación", "ok": bool(studies) and matched_studies == len(studies), "detail": f"Coinciden título e institución en {matched_studies} de {len(studies)} estudios guardados. Revisa si están terminados o en curso." if studies else "Revisa si tu formación se importó al perfil; también puedes registrar estudios en curso.", "target": "profile-educations", "action": "Revisar formación"},
        {"title": "Habilidades", "ok": bool(skills), "detail": "También aparecen en el documento: " + ", ".join(skills[:6]) + ". Una mención no demuestra dominio." if skills else "No encontramos coincidencias claras con tus habilidades guardadas. Revisa si faltan o si usan otros nombres.", "target": "profile-skills", "action": "Revisar habilidades"},
    ]


def select_jobs(jobs, search="", sector="", location="", now=None, recent_days=90):
    now = now or datetime.utcnow()
    terms = [word for word in re.findall(r"\w+", fold(search)) if len(word) > 1]
    selected, seen = [], set()
    for job in jobs:
        if job.status != "active" or job.expires_at and job.expires_at < now:
            continue
        if recent_days and job.created_at < now - timedelta(days=recent_days):
            continue
        if sector and fold(sector) not in fold(job.sector):
            continue
        if location and fold(location) not in fold(job.location):
            continue
        if terms and not all(term in fold(job.title) for term in terms):
            continue
        # Providers can mirror the same listing. Same company/title/location
        # counts once; no candidate profiles are used to compute demand.
        key = (fold(getattr(job, "company_name", "") or str(job.company_id)), fold(job.title), fold(job.location))
        if key not in seen:
            seen.add(key)
            selected.append(job)
    return sorted(selected, key=lambda job: (job.created_at, job.id), reverse=True)


def demand_report(profile, jobs, courses, search="", sector="", location="", now=None):
    now = now or datetime.utcnow()
    sample = select_jobs(jobs, search, sector, location, now)
    counts = Counter(skill_key(skill) for job in sample for skill in set(skill_key(value) for value in job.skills or []))
    known = skill_set(profile.skills)
    rows = []
    for skill, count in sorted(counts.items(), key=lambda row: (-row[1], row[0])):
        options = [resource for resource in courses if skill in skill_set(resource.get("skills", []))]
        rows.append({"skill": skill, "count": count, "percentage": round(count / len(sample) * 100) if len(sample) >= 5 else None,
                     "declared": skill in known, "courses": [{key: resource.get(key) for key in ("id", "title", "provider", "hours", "url")} for resource in options[:3]]})
    return {"sample": len(sample), "small_sample": len(sample) < 5, "since": (now - timedelta(days=90)).date().isoformat(),
            "as_of": now.isoformat() + "Z", "filters": {"search": search, "sector": sector, "location": location},
            "sources": dict(Counter(getattr(job, "source_name", None) or "TalentSync" for job in sample)), "skills": rows,
            "jobs": [{"id": job.id, "title": job.title, "location": job.location} for job in sample[:10]],
            "note": "Ofertas activas de los últimos 90 días, sin duplicados por empresa, cargo y ubicación. Mide demanda observada, no dominio de otros candidatos ni todo el mercado."}
