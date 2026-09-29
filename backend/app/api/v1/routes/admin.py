from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from app.api.deps import (
    get_adzuna_job_catalog,
    get_job_catalog,
    get_jsearch_job_catalog,
    get_resume_reader,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.api.schemas.admin import JobCatalogSyncRequest
from app.application.errors import UseCaseError
from app.application.ports.services import JobCatalog, ResumeReader, TextAnalysis
from app.application.ports.unit_of_work import UnitOfWork
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
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    search: str | None = Query(default=None, max_length=120),
    role: str | None = Query(default=None, pattern="^(candidate|company|admin)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    return use_cases.list_users(
        current_user=current_user,
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
    )


@router.get("/companies")
def list_admin_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    search: str | None = Query(default=None, max_length=120),
    scope: str = Query(default="platform", pattern="^(platform|external|all)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    return use_cases.list_admin_companies(
        current_user=current_user,
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        scope=scope,
    )


@router.get("/jobs")
def list_admin_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=5, le=100),
    search: str | None = Query(default=None, max_length=120),
    scope: str = Query(default="platform", pattern="^(platform|external|all)$"),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
) -> dict:
    return use_cases.list_admin_jobs(
        current_user=current_user,
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        scope=scope,
    )


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


@router.get("/jobs/sources/jooble")
def jooble_source_status(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    catalog: JobCatalog = Depends(get_job_catalog),
) -> dict:
    return {
        "source": "Jooble Colombia",
        "configured": catalog.configured,
        "registration_url": "https://co.jooble.org/api/about",
        "request_limit_note": (
            "Cada página sincronizada consume una solicitud de la cuota de Jooble."
        ),
    }


@router.post("/jobs/sources/jooble/sync")
def sync_jooble_jobs(
    payload: JobCatalogSyncRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    nlp: TextAnalysis = Depends(get_text_analysis),
    catalog: JobCatalog = Depends(get_job_catalog),
) -> dict:
    return job_imports.sync_job_catalog(
        keywords=payload.keywords,
        location=payload.location,
        pages=payload.pages,
        result_count=payload.result_count,
        current_user=current_user,
        db=db,
        nlp=nlp,
        catalog=catalog,
    )


def _source_status(catalog: JobCatalog, source: str) -> dict:
    missing = []
    if source == "Adzuna" and not catalog.configured:
        missing = ["ADZUNA_APP_ID", "ADZUNA_APP_KEY"]
    elif source == "JSearch" and not catalog.configured:
        missing = ["JSEARCH_API_KEY"]
    return {
        "source": source,
        "configured": catalog.configured,
        "registration_url": catalog.registration_url,
        "missing_settings": missing,
        "request_limit_note": "Cada búsqueda consume una solicitud de la cuota del proveedor.",
    }


@router.get("/jobs/sources/adzuna")
def adzuna_source_status(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    catalog: JobCatalog = Depends(get_adzuna_job_catalog),
) -> dict:
    return _source_status(catalog, "Adzuna")


@router.post("/jobs/sources/adzuna/sync")
def sync_adzuna_jobs(
    payload: JobCatalogSyncRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    nlp: TextAnalysis = Depends(get_text_analysis),
    catalog: JobCatalog = Depends(get_adzuna_job_catalog),
) -> dict:
    return job_imports.sync_job_catalog(
        keywords=payload.keywords,
        location=payload.location,
        pages=payload.pages,
        result_count=payload.result_count,
        current_user=current_user,
        db=db,
        nlp=nlp,
        catalog=catalog,
    )


@router.get("/jobs/sources/jsearch")
def jsearch_source_status(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    catalog: JobCatalog = Depends(get_jsearch_job_catalog),
) -> dict:
    return _source_status(catalog, "JSearch")


@router.post("/jobs/sources/jsearch/sync")
def sync_jsearch_jobs(
    payload: JobCatalogSyncRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: UnitOfWork = Depends(get_unit_of_work),
    nlp: TextAnalysis = Depends(get_text_analysis),
    catalog: JobCatalog = Depends(get_jsearch_job_catalog),
) -> dict:
    return job_imports.sync_job_catalog(
        keywords=payload.keywords,
        location=payload.location,
        pages=payload.pages,
        result_count=payload.result_count,
        current_user=current_user,
        db=db,
        nlp=nlp,
        catalog=catalog,
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
