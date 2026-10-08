from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_unit_of_work, require_roles
from app.api.schemas.organization import (
    AcceptInvitation,
    TeamInvitation,
    TeamUpdate,
    VerificationReview,
    VerificationSubmission,
)
from app.application.use_cases import organizations as cases
from app.core.config import settings
from app.core.limiter import limiter
from app.domain.entities.enums import UserRole

router = APIRouter()
company_user = require_roles(UserRole.COMPANY)
admin_user = require_roles(UserRole.ADMIN)


@router.get("/organization/me")
def organization(user=Depends(company_user), db=Depends(get_unit_of_work)):
    return cases.company_summary(db, user)


@router.post("/organization/verification")
def submit(payload: VerificationSubmission, user=Depends(company_user), db=Depends(get_unit_of_work)):
    return cases.submit_verification(db, user, payload.model_dump(mode="json"))


@router.get("/organization/team")
def team(user=Depends(company_user), db=Depends(get_unit_of_work)):
    return cases.team(db, user)


@router.post("/organization/invitations")
@limiter.limit("20/hour")
def invite(request: Request, payload: TeamInvitation, user=Depends(company_user), db=Depends(get_unit_of_work)):
    return cases.invite(db, user, payload.model_dump(), app_url=settings.public_app_url, mail_enabled=settings.local_mail_enabled)


@router.get("/organization/invitation")
@limiter.limit("60/hour")
def invitation(request: Request, token: str = Query(min_length=20, max_length=200), db=Depends(get_unit_of_work)):
    return cases.invitation_info(db, token)


@router.post("/organization/invitations/accept")
def accept(payload: AcceptInvitation, user=Depends(company_user), db=Depends(get_unit_of_work)):
    return cases.accept_invitation(db, user, payload.token)


@router.patch("/organization/team/{member_id}")
def update(member_id: int, payload: TeamUpdate, user=Depends(company_user), db=Depends(get_unit_of_work)):
    return cases.update_member(db, user, member_id, payload.model_dump())


@router.get("/organization/assignments")
def assignments(user=Depends(company_user), db=Depends(get_unit_of_work)):
    return cases.assignments(db, user)


@router.get("/admin/verifications")
def verifications(user=Depends(admin_user), db=Depends(get_unit_of_work)):
    return cases.verification_queue(db)


@router.post("/admin/verifications/{company_id}")
def review(company_id: int, payload: VerificationReview, user=Depends(admin_user), db=Depends(get_unit_of_work)):
    return cases.review_verification(db, user, company_id, payload.model_dump())
