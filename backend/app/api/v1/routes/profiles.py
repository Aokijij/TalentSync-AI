from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from app.api.deps import (
    get_career_writer,
    get_current_user,
    get_image_storage,
    get_resume_exporter,
    get_resume_previews,
    get_resume_reader,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.career_coach import (
    WritingDecision,
    WritingGeneration,
    WritingProposal,
)
from app.api.schemas.market import MarketFilters, MarketParticipation, MarketSkill
from app.api.schemas.professional_summary import SummaryGeneration
from app.api.schemas.profile import (
    CandidateProfileResponse,
    ProfileResponse,
    ProfileUpdate,
)
from app.api.schemas.resume_export import CvMentionDecision, ResumeDesign, ResumeExport
from app.application.errors import UseCaseError
from app.application.ports.services import ImageStorage, ResumeReader, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import career_coach as coach
from app.application.use_cases import market_radar, professional_summary
from app.application.use_cases import profiles as use_cases
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Profile, User
from app.domain.services.resume_filename import resume_disposition, resume_filename

router = APIRouter()


@router.post("/me/summary/generate")
def generate_summary(payload: SummaryGeneration, user=Depends(require_roles(UserRole.CANDIDATE)), writer=Depends(get_career_writer), nlp=Depends(get_text_analysis)):
    return professional_summary.generate(user, payload.model_dump(), writer=writer, nlp=nlp)


@router.get("/me/market")
def market_overview(filters: MarketFilters = Depends(), user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return market_radar.report(db, user, filters.model_dump(), local_fixture_mode=settings.environment == "development")


@router.put("/me/market/participation")
def market_participation(payload: MarketParticipation, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return market_radar.participate(db, user, payload.model_dump())


@router.post("/me/market/skills", response_model=ProfileResponse)
def market_skill(payload: MarketSkill, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return market_radar.declare_skill(db, user, payload.model_dump(), nlp)


@router.get("/me/coach")
def coach_overview(user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.overview(db, user)


@router.post("/me/coach/writing")
def coach_writing(payload: WritingProposal, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.prepare_writing(db, user, payload.model_dump())


@router.put("/me/coach/writing/{proposal_id}")
def coach_decide_writing(proposal_id: str, payload: WritingDecision, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.decide_writing(db, user, proposal_id, payload.model_dump())


@router.post("/me/coach/writing/generate")
def coach_generate_writing(payload: WritingGeneration, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work), writer=Depends(get_career_writer)):
    return coach.generate_writing(db, user, payload.model_dump(), writer=writer)


@router.delete("/me/coach/writing/{proposal_id}")
def coach_delete_writing(proposal_id: str, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.delete_writing(db, user, proposal_id)


@router.get("/me/coach/jobs/{job_id}/advice")
def coach_vacancy_advice(job_id: int, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.vacancy_advice(db, user, job_id)


@router.post("/me/coach/drafts")
@router.put("/me/coach/drafts/{draft_id}")
def coach_retired_preparation(user=Depends(require_roles(UserRole.CANDIDATE))):
    raise UseCaseError(status_code=410, detail="Las presentaciones por vacante se retiraron. Consulta los consejos para tu hoja de vida en la vacante")


@router.get("/me/coach/radar")
def coach_radar(search: str = "", sector: str = "", location: str = "", user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.radar(db, user, search[:160], sector[:120], location[:120])


@router.get("/me/coach/pdf")
def coach_pdf(user=Depends(require_roles(UserRole.CANDIDATE)), reader=Depends(get_resume_reader)):
    return Response(reader.original(coach.owner_profile(user)), media_type="application/pdf", headers={"Content-Disposition": 'inline; filename="cv-original.pdf"', "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/me/coach/reading")
def coach_reading(user=Depends(require_roles(UserRole.CANDIDATE)), reader=Depends(get_resume_reader)):
    from io import BytesIO

    from pypdf import PdfReader
    profile = coach.owner_profile(user)
    try:
        pdf = PdfReader(BytesIO(reader.original(profile)))
        pages = len(pdf.pages)
        text = (profile.preferences or {}).get("cv_source_text")
        stored = bool(text)
        method = "Texto usado en tu última importación"
        if not text:
            text = "\n\n".join(page.extract_text() or "" for page in pdf.pages[:20])
            method = "Lectura digital local del PDF guardado"
    except UseCaseError:
        raise
    except Exception:
        raise UseCaseError(status_code=422, detail="No fue posible leer este PDF") from None
    from app.domain.services.career_coach import document_review
    return {"text": text[:30000], "pages": pages, "truncated": len(text) >= 30000 or not stored and pages > 20, "method": method, "has_text": bool(text.strip()), "checks": document_review(profile, text[:30000]), "note": "Comparamos texto reconocible con tu perfil guardado. Estas comprobaciones pueden requerir revisión; no garantizan el resultado en otros sistemas. El texto se limita a 30.000 caracteres y la lectura de documentos antiguos a 20 páginas. Los PDF escaneados requieren OCR, todavía no disponible."}


@router.get("/me/coach/export")
def coach_retired_export(user=Depends(require_roles(UserRole.CANDIDATE))):
    raise UseCaseError(status_code=410, detail="Las versiones de PDF por vacante se retiraron. Puedes exportar tu hoja de vida desde Mi perfil")


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)) -> Profile:
    return use_cases.get_my_profile(current_user=current_user)


@router.patch("/me/cv-mentions", response_model=ProfileResponse)
def decide_cv_mention(payload: CvMentionDecision, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return use_cases.decide_cv_mention(db, user, payload.skill, payload.action, nlp=nlp)


@router.post("/me/export", response_class=Response)
def preview_resume_export(payload: ResumeExport, user=Depends(require_roles(UserRole.CANDIDATE)), exporter=Depends(get_resume_exporter)):
    from types import SimpleNamespace

    from app.domain.services.career_coach import snapshot
    profile = coach.owner_profile(user)
    values = {**snapshot(profile), "resume_style": profile.resume_style, "resume_color": profile.resume_color,
              "photo_filename": profile.photo_filename, "evidence": getattr(profile, "evidence", []), "links": getattr(profile, "links", [])}
    name = user.name
    if payload.profile:
        values.update(payload.profile.model_dump(mode="json", exclude={"name"} | {key for key in ("links", "driving_licenses", "professional_cards") if getattr(payload.profile, key) is None}))
        name = payload.profile.name or name
    document_user = SimpleNamespace(name=name, email=user.email, profile=SimpleNamespace(**values))
    return Response(exporter(document_user, sections=payload.sections, include_photo=payload.include_photo), media_type="application/pdf", headers={
        "Content-Disposition": resume_disposition(name, inline=True), "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.patch("/me/resume-design")
def save_resume_design(payload: ResumeDesign, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return use_cases.save_resume_design(db, user, payload.model_dump())


@router.post("/me/export/preview")
def create_named_preview(payload: ResumeExport, user=Depends(require_roles(UserRole.CANDIDATE)), exporter=Depends(get_resume_exporter), previews=Depends(get_resume_previews)):
    from urllib.parse import quote

    response = preview_resume_export(payload, user, exporter)
    filename = resume_filename(payload.profile.name if payload.profile and payload.profile.name else user.name)
    token = previews.put(user.id, response.body, filename)
    return {"url": f"/api/v1/profiles/me/export/preview/{token}/{quote(filename)}", "filename": filename}


@router.get("/me/export/preview/{token}/{filename}", response_class=Response)
def read_named_preview(token: str, filename: str, user=Depends(require_roles(UserRole.CANDIDATE)), previews=Depends(get_resume_previews)):
    return Response(previews.get(user.id, token, filename), media_type="application/pdf", headers={"Content-Disposition": resume_disposition(filename.removesuffix(" - TalentSync - Hoja de vida.pdf"), inline=True), "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/candidates/{user_id}", response_model=CandidateProfileResponse)
def get_candidate_profile(
    user_id: int,
    job_id: int | None = None,
    current_user: User = Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    return use_cases.get_candidate_profile(
        user_id=user_id, current_user=current_user, db=db, job_id=job_id
    )


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(require_roles(UserRole.CANDIDATE, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
) -> Profile:
    return use_cases.update_my_profile(
        payload=payload.model_dump(exclude={key for key in ("mobility", "birth_date") if key not in payload.model_fields_set}), current_user=current_user, db=db, nlp=nlp
    )


@router.post("/me/cv", response_model=ProfileResponse)
def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE, UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
    resumes: ResumeReader = Depends(get_resume_reader),
) -> Profile:
    return use_cases.upload_cv(
        file=file, current_user=current_user, db=db, nlp=nlp, resumes=resumes
    )


@router.post("/me/photo", response_model=ProfileResponse)
def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.CANDIDATE)),
    db: UnitOfWork = Depends(get_unit_of_work),
    storage: ImageStorage = Depends(get_image_storage),
) -> Profile:
    return use_cases.upload_photo(
        file=file, current_user=current_user, db=db, storage=storage
    )


@router.get("/{user_id}/photo", response_class=Response)
def get_profile_photo(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: UnitOfWork = Depends(get_unit_of_work),
    storage: ImageStorage = Depends(get_image_storage),
) -> Response:
    content, media_type = use_cases.profile_photo_content(
        user_id=user_id, current_user=current_user, db=db, storage=storage
    )
    return Response(content, media_type=media_type, headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/me/export", response_class=Response)
def export_resume(current_user: User = Depends(require_roles(UserRole.CANDIDATE)), exporter=Depends(get_resume_exporter)):
    return Response(exporter(current_user), media_type="application/pdf", headers={
        "Content-Disposition": resume_disposition(current_user.name),
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
