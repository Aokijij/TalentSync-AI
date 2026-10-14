"""Shared coach operations for any occupation; confirmed data is the source."""
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta

from app.domain.services.skill_context import fold
from app.domain.services.skills import skill_key, skill_set

PROFILE_FIELDS = ("profession", "skills", "experience", "education", "location", "department", "phone", "availability", "preferred_modality", "preferred_sector", "desired_salary", "experiences", "educations", "certifications", "languages")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def snapshot(profile):
    return json.loads(json.dumps({key: getattr(profile, key, None) for key in PROFILE_FIELDS}, default=str))


def job_version(job):
    return fingerprint([job.title, job.description, job.requirements, job.skills, getattr(job, "quality_revision", 0)])


def star_text(facts):
    values = [str(facts.get(key, "")).strip() for key in ("situation", "task", "action", "result")]
    if any(not value or re.search(r"\[[^\]]+\]", value) for value in values):
        raise ValueError("Completa los cuatro hechos con tus datos reales, sin marcadores pendientes")
    return " ".join(value if value[-1] in ".!?" else value + "." for value in values)


def vacancy_projection(profile, job):
    facts = snapshot(profile)
    known = skill_set(facts["skills"])
    supported = [skill for skill in job.skills or [] if skill_key(skill) in known]
    missing = [skill for skill in job.skills or [] if skill_key(skill) not in known]
    # An aspiration never changes a formal role or invents use of a tool.
    intro = f"{facts['profession'] or 'Candidato'}."
    if supported:
        intro += " Habilidades declaradas relacionadas con esta vacante: " + ", ".join(supported[:8]) + "."
    else:
        intro += " Revisa tus experiencias y explica qué aportes reales se relacionan con esta vacante."
    return {"profile": facts, "intro": intro, "supported_skills": supported, "questions": [f"¿Puedes respaldar {skill} con una experiencia o un proyecto real? Si no, consérvala como una brecha de formación." for skill in missing[:8]]}


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
    for skill, count in counts.most_common(12):
        options = [resource for resource in courses if skill in skill_set(resource.get("skills", []))]
        rows.append({"skill": skill, "count": count, "percentage": round(count / len(sample) * 100) if len(sample) >= 5 else None,
                     "declared": skill in known, "courses": [{key: resource.get(key) for key in ("id", "title", "provider", "hours", "url")} for resource in options[:3]]})
    return {"sample": len(sample), "small_sample": len(sample) < 5, "since": (now - timedelta(days=90)).date().isoformat(),
            "as_of": now.isoformat() + "Z", "filters": {"search": search, "sector": sector, "location": location},
            "sources": dict(Counter(getattr(job, "source_name", None) or "TalentSync" for job in sample)), "skills": rows,
            "jobs": [{"id": job.id, "title": job.title, "location": job.location} for job in sample[:10]],
            "note": "Ofertas activas de los últimos 90 días, sin duplicados por empresa, cargo y ubicación. Mide demanda observada, no dominio de otros candidatos ni todo el mercado."}
