from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import get_current_user, get_unit_of_work, require_roles
from app.api.schemas.organization import InterviewEvaluation
from app.application.use_cases import workflow as cases
from app.core.config import settings
from app.domain.entities.enums import UserRole

router = APIRouter()


@router.get("/workflow/applications/{application_id}")
def timeline(application_id: int, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.timeline(db, user, application_id)


@router.get("/workflow/applications/{application_id}/interview.ics")
def interview_calendar(application_id: int, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    content = cases.export_interview_calendar(db, user, application_id, public_app_url=settings.public_app_url)
    return Response(content=content, media_type="text/calendar; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="entrevista-talentsync-{application_id}.ics"',
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    })


@router.post("/workflow/applications/{application_id}/withdraw")
def withdraw(application_id: int, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return cases.withdraw(db, user, application_id)


@router.post("/admin/workflow/run")
def run(user=Depends(require_roles(UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return cases.deadline_cycle(db)


@router.post("/workflow/applications/{application_id}/evaluation")
def evaluate(application_id: int, payload: InterviewEvaluation, user=Depends(require_roles(UserRole.COMPANY)), db=Depends(get_unit_of_work)):
    return cases.evaluate_interview(db, user, application_id, payload.model_dump())
