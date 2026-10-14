from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from app.api.deps import (
    get_career_writer,
    get_current_user,
    get_image_storage,
    get_resume_exporter,
    get_resume_reader,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.career_coach import (
    DraftUpdate,
    VacancyDraft,
    WritingDecision,
    WritingGeneration,
    WritingProposal,
)
from app.api.schemas.profile import (
    CandidateProfileResponse,
    ProfileResponse,
    ProfileUpdate,
)
from app.application.errors import UseCaseError
from app.application.ports.services import ImageStorage, ResumeReader, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases import career_coach as coach
from app.application.use_cases import profiles as use_cases
from app.domain.entities.enums import UserRole
from app.domain.entities.records import Profile, User

router = APIRouter()


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


@router.get("/me/coach/jobs")
def coach_jobs(search: str = "", user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.jobs(db, search[:160])


@router.post("/me/coach/drafts")
def coach_prepare_draft(payload: VacancyDraft, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.prepare_draft(db, user, payload.job_id)


@router.put("/me/coach/drafts/{draft_id}")
def coach_update_draft(draft_id: str, payload: DraftUpdate, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return coach.update_draft(db, user, draft_id, payload.model_dump())


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
def coach_export(draft_id: str | None = None, application_id: int | None = None, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work), exporter=Depends(get_resume_exporter)):
    from types import SimpleNamespace

    from app.domain.services.career_coach import snapshot
    values = snapshot(coach.owner_profile(user))
    if draft_id:
        draft = coach.own_draft(db, user, draft_id)
        values = {**draft["profile"], "experience": draft["intro"]}
    if application_id:
        application = db.applications.get(application_id)
        if application is None or application.user_id != user.id or not application.coach_snapshot:
            raise UseCaseError(status_code=404, detail="Versión enviada no encontrada")
        saved = application.coach_snapshot
        values = {**saved["profile"], "experience": saved["intro"]}
    profile = coach.owner_profile(user)
    values.update(resume_style=profile.resume_style or "classic", resume_color=profile.resume_color or "default", evidence=[])
    pdf_user = SimpleNamespace(name=user.name, email=user.email, profile=SimpleNamespace(**values))
    return Response(exporter(pdf_user), media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="perfil-simple.pdf"', "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)) -> Profile:
    return use_cases.get_my_profile(current_user=current_user)


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
        payload=payload.model_dump(exclude={"mobility"} if "mobility" not in payload.model_fields_set else set()), current_user=current_user, db=db, nlp=nlp
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
        "Content-Disposition": 'attachment; filename="hoja-de-vida-talentsync.pdf"',
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
