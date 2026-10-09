from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, StrictFloat, StrictInt, StrictStr

from app.api.deps import get_text_analysis, get_unit_of_work, require_roles
from app.api.schemas.learning import ResourceContent, ResourceImport, ResourceUpdate
from app.application.use_cases import learning as cases
from app.application.use_cases import learning_resources
from app.domain.entities.enums import UserRole

router = APIRouter()
candidate = require_roles(UserRole.CANDIDATE)
admin = require_roles(UserRole.ADMIN)


class PlanUpdate(BaseModel):
    status: Literal["in_progress", "completed"] = "in_progress"


Answer = StrictInt | StrictFloat | Annotated[StrictStr, Field(max_length=100)] | Annotated[list[StrictInt], Field(max_length=10)]


class Submission(BaseModel):
    answers: dict[str, Answer] = Field(max_length=30)


class JourneyUpdate(BaseModel):
    version: StrictInt = Field(ge=1)
    answers: dict[str, Annotated[str, Field(max_length=550)]] = Field(default_factory=dict, max_length=3)
    activity_answers: dict[str, Answer] | None = Field(default=None, max_length=3)
    finish: bool = False
    add_to_profile: bool = False


@router.get("/learning/catalog")
def catalog(area: str = "recommended", user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.catalog(db, user, area)


@router.get("/admin/learning/resources")
def admin_resources(user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user)


@router.post("/admin/learning/resources", status_code=201)
def create_resource(payload: ResourceContent, user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user, [payload.model_dump()])


@router.post("/admin/learning/resources/import", status_code=201)
def import_resources(payload: ResourceImport, user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user, [row.model_dump() for row in payload.resources])


@router.put("/admin/learning/resources/{resource_id}")
def edit_resource(resource_id: str, payload: ResourceUpdate, user=Depends(admin), db=Depends(get_unit_of_work)):
    return learning_resources.manage(db, user, [payload.model_dump(exclude={"version"})], resource_id, payload.version)


@router.get("/learning/jobs/{job_id}")
def opportunities(job_id: int, user=Depends(candidate), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return cases.opportunities(db, user, job_id, nlp)


@router.get("/learning/plans")
def plans(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.plans(db, user)


@router.put("/learning/plans/{resource_id}")
def update_plan(resource_id: str, payload: PlanUpdate, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.plans(db, user, resource_id, payload.status)


@router.post("/learning/assessments/{assessment_id}/start")
def start(assessment_id: str, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.start_assessment(db, user, assessment_id)


@router.patch("/learning/plans/{resource_id}/journey")
def save_journey(resource_id: str, payload: JourneyUpdate, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.save_journey(db, user, resource_id, payload.model_dump())


@router.post("/learning/attempts/{attempt_id}/submit")
def submit(attempt_id: str, payload: Submission, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.submit_assessment(db, user, attempt_id, payload.answers)


@router.get("/learning/passport")
def passport(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.passport(db, user)


@router.get("/learning/patterns")
def patterns(user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.patterns(db, user)


@router.delete("/learning/plans/{resource_id}")
def leave_plan(resource_id: str, version: int, user=Depends(candidate), db=Depends(get_unit_of_work)):
    return cases.leave_plan(db, user, resource_id, version)
