from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import (
    get_current_user,
    get_text_analysis,
    get_unit_of_work,
    require_roles,
)
from app.application.use_cases import ecosystem as cases
from app.domain.entities.enums import UserRole

router = APIRouter()
admin = require_roles(UserRole.ADMIN)


class IncidentReport(BaseModel):
    application_id: int = Field(gt=0)
    category: Literal["ghosting", "inappropriate_interview", "suspected_fraud", "discrimination", "other"]
    details: str = Field(min_length=20, max_length=3000)


class IncidentReview(BaseModel):
    status: Literal["in_review", "confirmed", "dismissed"]
    shared_summary: str = Field(min_length=10, max_length=1500)


class Appeal(BaseModel):
    message: str = Field(min_length=20, max_length=3000)


@router.get("/trust/companies/{company_id}")
def trust(company_id: int, user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.trust(db, company_id)


@router.post("/trust/incidents")
def report(payload: IncidentReport, user=Depends(require_roles(UserRole.CANDIDATE)), db=Depends(get_unit_of_work)):
    return cases.report_incident(db, user, payload.model_dump())


@router.get("/trust/incidents/me")
def own(user=Depends(get_current_user), db=Depends(get_unit_of_work)):
    return cases.incidents(db, user, "own")


@router.get("/trust/organization/incidents")
def organization(user=Depends(require_roles(UserRole.COMPANY)), db=Depends(get_unit_of_work)):
    return cases.incidents(db, user, "organization")


@router.post("/trust/incidents/{incident_id}/appeal")
def appeal(incident_id: int, payload: Appeal, user=Depends(require_roles(UserRole.COMPANY)), db=Depends(get_unit_of_work)):
    return cases.appeal(db, user, incident_id, payload.message)


@router.get("/admin/incidents")
def all_incidents(user=Depends(admin), db=Depends(get_unit_of_work)):
    return cases.incidents(db, user, "admin")


@router.patch("/admin/incidents/{incident_id}")
def review(incident_id: int, payload: IncidentReview, user=Depends(admin), db=Depends(get_unit_of_work)):
    return cases.review(db, user, incident_id, payload.model_dump())


@router.get("/admin/incident-queue")
def incident_queue(
    bucket: Literal["pending", "resolved", "all"] = "pending",
    status: Literal["all", "open", "in_review", "confirmed", "dismissed", "appealed"] = "all",
    category: Literal["all", "ghosting", "inappropriate_interview", "suspected_fraud", "discrimination", "other"] = "all",
    search: str = Query(default="", max_length=120),
    sort: Literal["priority", "oldest", "newest"] = "priority",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
    user=Depends(admin), db=Depends(get_unit_of_work),
):
    return cases.incident_queue(db, bucket=bucket, status=status, category=category, search=search.strip(), sort=sort, page=page, page_size=page_size)


@router.get("/admin/incidents/{incident_id}")
def incident_detail(incident_id: int, user=Depends(admin), db=Depends(get_unit_of_work)):
    return cases.incident_detail(db, incident_id)


@router.get("/admin/ecosystem")
def dashboard(include_companies: bool = True, user=Depends(admin), db=Depends(get_unit_of_work)):
    return cases.dashboard(db, include_companies=include_companies)


@router.get("/admin/company-directory")
def company_directory(search: str = Query(default="", max_length=120),
                      filter: Literal["all", "attention", "rated", "unrated"] = "all",
                      page: int = Query(default=1, ge=1), page_size: int = Query(default=6, ge=1, le=50),
                      user=Depends(admin), db=Depends(get_unit_of_work)):
    return cases.company_directory(db, search=search.strip(), filter=filter, page=page, page_size=page_size)


@router.post("/admin/ecosystem/audit")
def audit(user=Depends(admin), db=Depends(get_unit_of_work), nlp=Depends(get_text_analysis)):
    return cases.run_audit(db, user, nlp)
