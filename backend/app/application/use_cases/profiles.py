from datetime import datetime
from typing import Any

from app.application.errors import UseCaseError
from app.application.ports.services import ResumeReader, TextAnalysis, UploadedResume
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Profile, User
from app.domain.services.skills import normalize_skills


def company_can_view_candidate(
    db: UnitOfWork, company_user: User, candidate_id: int
) -> bool:
    company = db.companies.find_by_owner(company_user.id)
    if company is None:
        return False
    return (
        db.applications.find_for_candidate_company(candidate_id, company.id) is not None
    )


def get_my_profile(current_user: User) -> Profile:
    return current_user.profile


def get_candidate_profile(user_id: int, current_user: User, db: UnitOfWork) -> dict:
    candidate = db.users.get(user_id)
    if (
        candidate is None
        or candidate.role != UserRole.CANDIDATE
        or candidate.profile is None
    ):
        raise UseCaseError(status_code=404, detail="Perfil de candidato no encontrado")
    if current_user.role == UserRole.COMPANY and (
        not company_can_view_candidate(db, current_user, user_id)
    ):
        raise UseCaseError(
            status_code=403,
            detail="Solo puedes ver el perfil completo de candidatos que se postularon a tus vacantes",
        )
    profile = candidate.profile
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": candidate.name,
        "email": candidate.email,
        "profession": profile.profession,
        "skills": profile.skills or [],
        "experience": profile.experience,
        "education": profile.education,
        "location": profile.location,
        "department": profile.department,
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
    }


def update_my_profile(
    payload: dict[str, Any], current_user: User, db: UnitOfWork, *, nlp: TextAnalysis
) -> Profile:
    profile = current_user.profile or db.profiles.new(user_id=current_user.id)
    profile.profession = payload["profession"]
    profile.skills = normalize_skills(payload["skills"])
    profile.experience = payload["experience"]
    profile.education = payload["education"]
    profile.location = payload["location"]
    profile.department = payload["department"]
    profile.availability = payload["availability"]
    profile.preferred_modality = payload["preferred_modality"]
    profile.preferred_sector = payload["preferred_sector"]
    profile.desired_salary = payload["desired_salary"]
    profile.phone = payload["phone"]
    profile.experiences = payload["experiences"] or []
    profile.educations = payload["educations"] or []
    profile.certifications = payload["certifications"] or []
    text = " ".join(
        filter(
            None,
            [
                payload["profession"],
                " ".join(profile.skills),
                payload["experience"],
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
    profile.experiences = analysis.experiences or profile.experiences or []
    profile.educations = analysis.educations or profile.educations or []
    profile.certifications = analysis.certifications or profile.certifications or []
    profile.embedding = analysis.embedding
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
