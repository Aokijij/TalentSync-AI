from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.ports.services import (
    ImageStorage,
    ResumeReader,
    TextAnalysis,
    UploadedResume,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Profile, User
from app.domain.services.blind_hiring import candidate_alias, identity_hidden
from app.domain.services.skill_levels import declared_skill_levels
from app.domain.services.skills import normalize_skills


def company_can_view_candidate(
    db: UnitOfWork, company_user: User, candidate_id: int
) -> bool:
    company = db.companies.find_by_owner(company_user.id)
    if company is None:
        return False
    return any(row.user_id == candidate_id and not identity_hidden(job, row) for job in company.jobs for row in job.applications)


def get_my_profile(current_user: User) -> Profile:
    return current_user.profile


def decide_cv_mention(db, user, skill, action, *, nlp):
    from app.domain.services.skill_context import profile_skill_context
    from app.domain.services.skills import skill_key
    profile = user.profile
    if profile is None:
        raise UseCaseError(status_code=404, detail="Completa primero tu perfil")
    db.profiles.lock_owner(user.id)
    db.refresh(profile)
    key = skill_key(skill)
    mention = next((row for row in profile_skill_context(profile) if skill_key(row.get("skill", "")) == key), None)
    if mention is None:
        raise UseCaseError(status_code=404, detail="Esta mención ya no está disponible. Actualiza tu perfil")
    decisions = dict((profile.preferences or {}).get("cv_mention_decisions", {}))
    if action == "restore":
        decisions.pop(key, None)
    elif action == "confirm":
        profile.skills = normalize_skills([*(profile.skills or []), mention["skill"]])
        decisions[key] = "confirmed"
        profile.embedding = nlp.embed(" ".join(filter(None, [profile.profession, profile.experience, " ".join(profile.skills)])))
    else:
        decisions[key] = "dismissed"
    profile.preferences = {**(profile.preferences or {}), "cv_mention_decisions": decisions}
    db.add(profile); db.commit(); db.refresh(profile)
    return profile


def build_professional_summary(profile: Profile, fallback: str | None = None) -> str | None:
    """Build a short CV overview without repeating employer names."""
    profession = (profile.profession or "").strip()
    roles = []
    for item in profile.experiences or []:
        role = str(item.get("role") or "").strip()
        if role and role.casefold() not in {value.casefold() for value in roles}:
            roles.append(role)
    skills = [str(value).strip() for value in (profile.skills or []) if str(value).strip()]
    education = next(
        (
            str(item.get("degree") or "").strip()
            for item in (profile.educations or [])
            if str(item.get("degree") or "").strip()
        ),
        "",
    )

    sentences: list[str] = []
    if profession and roles:
        sentences.append(
            f"{profession} con experiencia en {', '.join(roles[:3])}."
        )
    elif profession:
        sentences.append(f"Perfil profesional en {profession}.")
    elif roles:
        sentences.append(f"Experiencia en {', '.join(roles[:3])}.")

    if skills:
        sentences.append(f"Fortalezas en {', '.join(skills[:6])}.")
    if education:
        sentences.append(f"Formación en {education}.")
    if profile.preferred_sector:
        sentences.append(
            f"Interés en oportunidades del sector {profile.preferred_sector.lower()}."
        )

    summary = " ".join(sentences).strip()
    if not summary:
        return fallback.strip() if fallback and fallback.strip() else None
    return summary[:600].rstrip()


def get_candidate_profile(user_id: int, current_user: User, db: UnitOfWork, job_id: int | None = None) -> dict:
    application = None
    candidate = db.users.get(user_id)
    if (
        candidate is None
        or candidate.role != UserRole.CANDIDATE
        or candidate.profile is None
    ):
        raise UseCaseError(status_code=404, detail="Perfil de candidato no encontrado")
    if current_user.role == UserRole.COMPANY and job_id is not None:
        company = db.companies.find_by_owner(current_user.id)
        job = db.jobs.get(job_id)
        application = next((row for row in job.applications if row.user_id == user_id), None) if job else None
        if not company or not job or job.company_id != company.id or application is None:
            raise UseCaseError(status_code=403, detail="El perfil debe pertenecer a una postulación de esta vacante")
        if identity_hidden(job, application):
            profile = _submitted_profile(candidate.profile, application)
            # Do not include CV text, names of employers/schools, descriptions or contact data.
            # Identity visibility is scoped to this process, even if another job revealed it.
            return {
                "id": profile.id, "user_id": user_id, "name": candidate_alias(job_id, user_id),
                "identity_hidden": True, "profession": profile.profession,
                "skills": profile.skills or [], "skill_levels": declared_skill_levels(profile), "languages": profile.languages or [],
                "availability": profile.availability, "preferred_modality": profile.preferred_modality,
                "desired_salary": profile.desired_salary,
                "experiences": [{key: row.get(key) for key in ("role", "start_year", "end_year", "start_date", "end_date", "is_current")} for row in profile.experiences or []],
                "educations": [{key: row.get(key) for key in ("degree", "start_year", "end_year", "is_current")} for row in profile.educations or []],
            }
    if current_user.role == UserRole.COMPANY and (
        not company_can_view_candidate(db, current_user, user_id)
    ):
        raise UseCaseError(
            status_code=403,
            detail="Solo puedes ver el perfil completo de candidatos que se postularon a tus vacantes",
        )
    profile = _submitted_profile(candidate.profile, application)
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": candidate.name,
        "email": candidate.email,
        "profession": profile.profession,
        "skills": profile.skills or [],
        "skill_levels": declared_skill_levels(profile),
        "languages": profile.languages or [],
        "experience": profile.experience,
        "education": profile.education,
        "location": profile.location,
        "department": profile.department,
        "mobility": (profile.preferences or {}).get("mobility", {}),
        "availability": profile.availability,
        "preferred_modality": profile.preferred_modality,
        "preferred_sector": profile.preferred_sector,
        "desired_salary": profile.desired_salary,
        "phone": profile.phone,
        "experiences": profile.experiences or [],
        "educations": profile.educations or [],
        "certifications": profile.certifications or [],
        "cv_text": profile.cv_text,
        "cv_filename": profile.cv_filename,
        "cv_uploaded_at": profile.cv_uploaded_at,
        "photo_url": profile.photo_url,
        "resume_style": profile.resume_style,
        "resume_color": profile.resume_color,
        "submitted_version": (getattr(application, "coach_snapshot", None) or {}).get("draft_id") if application else None,
    }


def _submitted_profile(profile, application):
    from types import SimpleNamespace
    saved = (getattr(application, "coach_snapshot", None) or {}) if application else {}
    if not saved.get("profile"):
        return profile
    return SimpleNamespace(**{**saved["profile"], "experience": saved["intro"], "id": profile.id, "user_id": profile.user_id,
                              "cv_text": None, "cv_filename": None, "cv_uploaded_at": None, "photo_url": None,
                              "resume_style": "minimal", "resume_color": "default", "preferences": {}})


def save_resume_design(db, user, payload):
    from app.application.use_cases.career_coach import owner_profile

    profile = owner_profile(user)
    db.profiles.lock_owner(user.id); db.refresh(profile)
    profile.resume_style, profile.resume_color = payload["style"], payload["color"]
    options = {"sections": list(dict.fromkeys(payload["sections"])), "include_photo": payload["include_photo"]}
    profile.preferences = {**(profile.preferences or {}), "resume_export_options": options}
    db.add(profile); db.commit()
    return {"resume_style": profile.resume_style, "resume_color": profile.resume_color, "resume_export_options": options}


def update_my_profile(
    payload: dict[str, Any], current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
) -> Profile:
    profile = current_user.profile or db.profiles.new(user_id=current_user.id)
    requested_name = (payload.pop("name", None) or "").strip()
    if requested_name:
        current_user.name = requested_name
        db.add(current_user)
    profile.profession = payload["profession"]
    profile.skills = normalize_skills(payload["skills"])
    supplied_levels = payload.get("skill_levels")
    if supplied_levels is not None:
        profile.preferences = {**(profile.preferences or {}), "skill_levels": supplied_levels}
    profile.preferences = {**(profile.preferences or {}), "skill_levels": declared_skill_levels(profile)}
    profile.languages = payload.get("languages", [])
    previous_summary = payload["experience"]
    profile.education = payload["education"]
    profile.location = payload["location"]
    profile.department = payload["department"]
    profile.availability = payload["availability"]
    profile.preferred_modality = payload["preferred_modality"]
    profile.preferred_sector = payload["preferred_sector"]
    profile.desired_salary = payload["desired_salary"]
    profile.phone = payload["phone"]
    profile.experiences = payload["experiences"] or []
    if "mobility" in payload:
        profile.preferences = {**(profile.preferences or {}), "mobility": payload["mobility"]}
    profile.educations = payload["educations"] or []
    profile.certifications = payload["certifications"] or []
    profile.resume_style = payload["resume_style"]
    profile.resume_color = payload.get("resume_color", "default")
    profile.experience = build_professional_summary(profile, previous_summary)
    text = " ".join(
        filter(
            None,
            [
                payload["profession"],
                " ".join(profile.skills),
                profile.experience,
                payload["education"],
                payload["location"],
                payload["department"],
                payload["preferred_sector"],
            ],
        )
    )
    profile.embedding = nlp.embed(text)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def upload_photo(
    file, current_user: User, db: UnitOfWork, *, storage: ImageStorage
) -> Profile:
    allowed_types = {
        "image/jpeg": ("jpg", b"\xff\xd8\xff"),
        "image/png": ("png", b"\x89PNG\r\n\x1a\n"),
        "image/webp": ("webp", b"RIFF"),
    }
    image_type = allowed_types.get(file.content_type or "")
    if image_type is None:
        raise UseCaseError(
            status_code=400, detail="La foto debe ser JPG, PNG o WebP"
        )
    extension, signature = image_type
    content = file.file.read(3 * 1024 * 1024 + 1)
    if not content:
        raise UseCaseError(status_code=400, detail="La imagen está vacía")
    if len(content) > 3 * 1024 * 1024:
        raise UseCaseError(status_code=400, detail="La imagen no puede superar 3 MB")
    if not content.startswith(signature) or (
        extension == "webp" and content[8:12] != b"WEBP"
    ):
        raise UseCaseError(status_code=400, detail="El archivo no es una imagen válida")

    profile = current_user.profile or db.profiles.new(user_id=current_user.id)
    filename = f"user_{current_user.id}_{uuid4().hex}.{extension}"
    storage.save("profile_photos", filename, content, file.content_type)
    profile.photo_filename = filename
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def profile_photo_content(
    user_id: int, current_user: User, db: UnitOfWork, *, storage: ImageStorage
) -> tuple[bytes, str]:
    can_view = (
        current_user.id == user_id
        or current_user.role == UserRole.ADMIN
        or (
            current_user.role == UserRole.COMPANY
            and company_can_view_candidate(db, current_user, user_id)
        )
    )
    if not can_view:
        raise UseCaseError(status_code=403, detail="No puedes consultar esta foto")
    user = db.users.get(user_id)
    profile = user.profile if user else None
    if profile is None or not profile.photo_filename:
        raise UseCaseError(status_code=404, detail="Foto de perfil no encontrada")
    filename = Path(profile.photo_filename).name
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(Path(filename).suffix.lower(), "application/octet-stream")
    return storage.read("profile_photos", filename), media_type


def upload_cv(
    file: UploadedResume,
    current_user: User,
    db: UnitOfWork,
    *,
    nlp: TextAnalysis,
    resumes: ResumeReader,
) -> Profile:
    safe_name, raw_text = resumes.extract(file, current_user.id)
    analysis = nlp.analyze_cv(raw_text)
    profile = current_user.profile or db.profiles.new(user_id=current_user.id)
    profile.cv_text = analysis.clean_text
    profile.cv_filename = safe_name
    profile.cv_uploaded_at = datetime.utcnow()
    from app.domain.services.skill_context import CONTEXT_VERSION
    profile.preferences = {**{key: value for key, value in (profile.preferences or {}).items() if key != "cv_entity_review"},
                           "cv_skill_context": getattr(analysis, "skill_context", []), "cv_context_version": CONTEXT_VERSION,
                           "cv_source_text": raw_text[:30000]}
    profile.profession = analysis.profession or profile.profession
    profile.skills = normalize_skills([*(profile.skills or []), *analysis.skills])
    profile.experience = analysis.experience or profile.experience
    profile.education = analysis.education or profile.education
    if analysis.location:
        location_parts = [part.strip() for part in analysis.location.split(",", 1)]
        profile.location = location_parts[0]
        if len(location_parts) == 2:
            profile.department = location_parts[1]
    profile.phone = analysis.phone or profile.phone
    profile.experiences = _merge_imported(profile.experiences, analysis.experiences, ("role", "company"))
    profile.educations = _merge_imported(profile.educations, analysis.educations, ("degree", "institution"))
    profile.certifications = _merge_imported(profile.certifications, analysis.certifications, ("name", "issuer"))
    if analysis.experiences:
        profile.experience = build_professional_summary(
            profile, analysis.experience or profile.experience
        )
    profile.embedding = analysis.embedding
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _merge_imported(existing, detected, keys):
    from app.domain.services.skill_context import fold
    merged = [dict(row) for row in existing or []]
    for row in detected or []:
        identity = tuple(fold(row.get(key)) for key in keys)
        def same_record(item):
            if tuple(fold(item.get(key)) for key in keys) != identity:
                return False
            if keys == ("role", "company"):
                start_a, end_a = item.get("start_date") or item.get("start_year"), item.get("end_date") or item.get("end_year")
                start_b, end_b = row.get("start_date") or row.get("start_year"), row.get("end_date") or row.get("end_year")
                if all(value and str(value)[:4].isdigit() for value in (start_a, end_a, start_b, end_b)):
                    # Separate rehires, while retaining confirmed fields when
                    # the imported period overlaps the existing employment.
                    return not (str(end_a)[:4] < str(start_b)[:4] or str(end_b)[:4] < str(start_a)[:4])
            return True
        previous = next((item for item in merged if same_record(item)), None)
        if previous is None:
            incoming = dict(row)
            if keys == ("role", "company") and incoming.get("is_current") and any(item.get("is_current") for item in merged):
                incoming.update(is_current=False, end_date=None, end_year="", date_review_required=True)
            merged.append(incoming)
        else:
            # Keep manually confirmed content and supplied certificate links.
            previous.update({key: value for key, value in row.items() if previous.get(key) in (None, "", [])})
    return merged
