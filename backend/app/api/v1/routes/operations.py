from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import (
    get_calendar_gateway,
    get_request_metrics,
    get_resume_reader,
    get_unit_of_work,
    require_roles,
)
from app.application.use_cases import operations as cases
from app.core.config import settings
from app.domain.entities.enums import UserRole

router = APIRouter()
health_router = APIRouter()


@health_router.get("/health/live", tags=["health"])
def live():
    return {"status": "alive"}


@health_router.get("/health/ready", tags=["health"])
def ready(db=Depends(get_unit_of_work), storage=Depends(get_resume_reader)):
    result = cases.readiness(db, storage)
    return JSONResponse(result, status_code=200 if result["status"] == "ready" else 503, headers={"Cache-Control": "no-store"})


@router.get("/admin/operations")
def status(user=Depends(require_roles(UserRole.ADMIN)), db=Depends(get_unit_of_work), storage=Depends(get_resume_reader), metrics=Depends(get_request_metrics), calendar=Depends(get_calendar_gateway)):
    return cases.status(db, storage, metrics, calendar_configured=calendar.configured, retention_enabled=settings.account_retention_enabled, cleanup_enabled=settings.account_cleanup_enabled)
