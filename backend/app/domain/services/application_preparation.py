"""Preparation from saved facts, without an external model or invented answers."""
import json
from copy import deepcopy

from app.domain.services.career_coach import fingerprint, snapshot
from app.domain.services.personal_details import shared_personal_details
from app.domain.services.skill_context import fold
from app.domain.services.skills import skill_key


def resume_profile(profile):
    values = snapshot(profile)
    for key in ("links", "evidence", "resume_style", "resume_color", "photo_filename"):
        values[key] = getattr(profile, key, None)
    visibility = getattr(profile, "personal_visibility", None) or {}
    values.update(shared_personal_details(profile))
    values["personal_visibility"] = visibility
    values["preferences"] = {key: deepcopy((getattr(profile, "preferences", None) or {}).get(key, {})) for key in ("skill_levels", "mobility")}
    return json.loads(json.dumps(values, default=str))


def source_version(user):
    return fingerprint({"name": user.name, "email": user.email, "profile": resume_profile(user.profile)})


def job_snapshot(job):
    return {"id": job.id, "title": job.title, "company_name": job.company_name,
            **{key: deepcopy(getattr(job, key, None)) for key in ("description", "requirements", "skills", "skill_requirements", "location", "modality", "required_education_level", "required_study_fields", "languages")}}


def suggested_skills(profile, job):
    requested = {skill_key(skill) for skill in job.get("skills") or []}
    return sorted(profile.get("skills") or [], key=lambda skill: skill_key(skill) not in requested)


def interview_questions(profile, job):
    experiences = profile.get("experiences") or []
    skills = list({skill_key(skill): skill for skill in job.get("skills") or []}.values())[:4]
    questions = [
        {"id": "introduction", "title": f"¿Qué parte de tu trayectoria te prepara para {job['title']}?", "hint": "Elige una experiencia, práctica o proyecto real y explica su relación con las responsabilidades del cargo."},
        {"id": "problem", "title": "Cuéntame cómo resolviste una dificultad en un trabajo o proyecto.", "hint": "Explica qué hiciste tú, qué entregaste y qué aprendiste. El resultado puede ser cualitativo."},
    ]
    own = {skill_key(skill) for skill in profile.get("skills") or []}
    for skill in skills:
        questions.append({"id": "skill-" + fingerprint(skill_key(skill))[:16], "skill": skill,
            "title": f"¿Cómo has utilizado {skill} y qué resultado obtuviste?",
            "hint": "Busca un ejemplo real. Si no la has usado, explica lo que aún necesitas aprender y una experiencia relacionada.",
            "in_profile": skill_key(skill) in own})
    questions.append({"id": "collaboration", "title": "¿Cómo coordinaste una entrega o resolviste un desacuerdo con otras personas?", "hint": "Describe tu participación y cómo comprobaron el resultado."})
    for question in questions:
        skill = question.get("skill")
        matches = [row for row in experiences if not skill or fold(skill) in fold(str(row.get("description") or ""))]
        question["experiences"] = [{key: row.get(key) for key in ("role", "company", "description")} for row in matches[:2]]
    return questions


def preparation_revision(profile, job):
    # Private personal details do not influence questions or preparation.
    return fingerprint({"job": job, "profile": {key: profile.get(key) for key in ("profession", "skills", "experience", "experiences", "educations")}})


def answer_review(answer):
    labels = {"situation": "contexto", "task": "responsabilidad", "action": "acción", "result": "resultado"}
    missing = [label for key, label in labels.items() if not str(answer.get(key) or "").strip()]
    return {"complete": not missing, "missing": missing}
