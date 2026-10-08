from fastapi import APIRouter, Depends

from app.api.deps import get_unit_of_work, require_roles
from app.application.use_cases import hiring as cases
from app.domain.entities.enums import UserRole

router = APIRouter()


@router.get("/hiring/quality/{job_id}")
def quality(job_id: int, user=Depends(require_roles(UserRole.COMPANY, UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    return cases.quality(db, user, job_id)
