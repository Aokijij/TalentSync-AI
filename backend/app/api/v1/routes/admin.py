from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from app.api.deps import (
    get_resume_reader,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.application.ports.services import ResumeReader, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
from app.application.errors import UseCaseError
from app.application.use_cases import admin as use_cases
from app.application.use_cases import job_imports
from app.domain.entities.enums import UserRole
from app.domain.entities.records import User

router = APIRouter()

MAX_IMPORT_BYTES = 5 * 1024 * 1024


@router.get("/stats")
def platform_stats(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict[str, int]:
    return use_cases.platform_stats(current_user=current_user, db=db)


@router.get("/analytics")
def platform_analytics(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    *,
    nlp: TextAnalysis = Depends(get_text_analysis),
    resumes: ResumeReader = Depends(get_resume_reader),
) -> dict:
    """Operational analytics used by the live administration dashboard."""
    return use_cases.platform_analytics(
        current_user=current_user, db=db, nlp=nlp, resumes=resumes
    )


@router.get("/users")
def list_users(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[dict]:
    return use_cases.list_users(current_user=current_user, db=db)


@router.get("/companies")
def list_admin_companies(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[dict]:
    return use_cases.list_admin_companies(current_user=current_user, db=db)


@router.get("/jobs")
def list_admin_jobs(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> list[dict]:
    return use_cases.list_admin_jobs(current_user=current_user, db=db)


@router.get("/jobs/import-template")
def download_job_import_template(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    return Response(
        content=job_imports.template_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="plantilla-vacantes-talentsync.csv"'
        },
    )


@router.post("/jobs/import")
async def import_external_jobs(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    nlp: TextAnalysis = Depends(get_text_analysis),
) -> dict:
    content = await file.read(MAX_IMPORT_BYTES + 1)
    if not content:
        raise UseCaseError(status_code=400, detail="El archivo está vacío")
    if len(content) > MAX_IMPORT_BYTES:
        raise UseCaseError(
            status_code=400, detail="El archivo no puede superar 5 MB"
        )
    return job_imports.import_jobs(
        file.filename or "",
        content,
        current_user,
        db,
        nlp=nlp,
    )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_job(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    return use_cases.delete_admin_job(job_id=job_id, current_user=current_user, db=db)


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_company(
    company_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    return use_cases.delete_admin_company(
        company_id=company_id, current_user=current_user, db=db
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_user(
    user_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> None:
    return use_cases.delete_admin_user(
        user_id=user_id, current_user=current_user, db=db
    )
