from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_unit_of_work, require_roles
from app.application.use_cases import workflow as cases
from app.domain.entities.enums import UserRole

router = APIRouter()


@router.get("/workflow/applications/{application_id}")
def timeline(application_id: int, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.timeline(db, user, application_id)


@router.post("/workflow/applications/{application_id}/withdraw")
def withdraw(application_id: int, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return cases.withdraw(db, user, application_id)


@router.post("/admin/workflow/run")
def run(user=Depends(require_roles(UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return cases.deadline_cycle(db)
