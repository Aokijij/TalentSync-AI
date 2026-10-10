from datetime import datetime

from sqlalchemy import case, func, or_, update
from sqlalchemy.orm import joinedload

from app.infrastructure.database.models import (
    Company,
    CompanyInvitation,
    CompanyMember,
    User,
)
from app.infrastructure.repositories.paging import query_page


class OrganizationRepository:
    def __init__(self, session):
        self.session = session

    def member_for_user(self, user_id):
        return self.session.query(CompanyMember).filter_by(user_id=user_id).first()

    def members(self, company_id):
        return self.session.query(CompanyMember).filter_by(company_id=company_id).all()

    def member(self, company_id, member_id):
        return self.session.query(CompanyMember).filter_by(company_id=company_id, id=member_id).first()

    def team_page(self, company_id, *, kind, status, search, page, page_size):
        now = datetime.utcnow()
        members = self.session.query(CompanyMember).filter_by(company_id=company_id)
        invitations = self.session.query(CompanyInvitation).filter_by(company_id=company_id)
        invitation_state = case((CompanyInvitation.used_at.is_not(None), "accepted"), (CompanyInvitation.expires_at <= now, "expired"), else_="pending")
        member_counts = dict(members.with_entities(CompanyMember.active, func.count()).group_by(CompanyMember.active).all())
        invitation_counts = dict(invitations.with_entities(invitation_state, func.count()).group_by(invitation_state).all())
        if kind == "members":
            query = members.join(User, User.id == CompanyMember.user_id).with_entities(CompanyMember.id, CompanyMember.user_id, User.name, User.email, CompanyMember.role, CompanyMember.active, CompanyMember.assigned_job_ids)
            if status != "all":
                query = query.filter(CompanyMember.active.is_(status == "active"))
            fields = [User.name, User.email, CompanyMember.role]
            role_column = CompanyMember.role
            query = query.order_by(CompanyMember.active.desc(), func.lower(User.name), CompanyMember.id)
        else:
            query = invitations.with_entities(CompanyInvitation.id, CompanyInvitation.email, CompanyInvitation.role, CompanyInvitation.assigned_job_ids, CompanyInvitation.expires_at, invitation_state.label("status"))
            if status != "all":
                query = query.filter(invitation_state == status)
            fields = [CompanyInvitation.email, CompanyInvitation.role]
            role_column = CompanyInvitation.role
            query = query.order_by(CompanyInvitation.id.desc())
        if search:
            terms = [func.lower(field).contains(search.lower(), autoescape=True) for field in fields]
            role = {"reclutador": "recruiter", "entrevistador": "interviewer"}.get(search.lower())
            if role:
                terms.append(role_column == role)
            query = query.filter(or_(*terms))
        result = query_page(query, page=page, page_size=page_size)
        result["items"] = [row._asdict() for row in result["items"]]
        result["counts"] = {"active": member_counts.get(True, 0), "revoked": member_counts.get(False, 0),
                            "members": sum(member_counts.values()), "invitations": sum(invitation_counts.values()), **{key: invitation_counts.get(key, 0) for key in ("pending", "accepted", "expired")}}
        return result

    def new_member(self, **values):
        return CompanyMember(**values)

    def new_invitation(self, **values):
        return CompanyInvitation(**values)

    def invitation(self, digest):
        return self.session.query(CompanyInvitation).filter_by(token_hash=digest).first()

    def invitations(self, company_id):
        return self.session.query(CompanyInvitation).filter_by(company_id=company_id).order_by(CompanyInvitation.id.desc()).limit(200).all()

    def cancel_invitation(self, company_id, invitation_id):
        result = self.session.execute(update(CompanyInvitation).where(
            CompanyInvitation.id == invitation_id, CompanyInvitation.company_id == company_id,
            CompanyInvitation.used_at.is_(None), CompanyInvitation.expires_at > datetime.utcnow(),
        ).values(expires_at=datetime.utcnow()).execution_options(synchronize_session=False))
        return result.rowcount == 1

    def consume_invitation(self, invitation_id):
        result = self.session.execute(update(CompanyInvitation).where(
            CompanyInvitation.id == invitation_id, CompanyInvitation.used_at.is_(None),
            CompanyInvitation.expires_at > datetime.utcnow(),
        ).values(used_at=datetime.utcnow()).execution_options(synchronize_session=False))
        return result.rowcount == 1

    def verification_queue(self):
        return self.session.query(Company).filter(Company.verification_required.is_(True)).order_by(Company.id.desc()).limit(200).all()

    def verification_page(self, *, status, search, page, page_size):
        query = self.session.query(Company).filter(Company.verification_required.is_(True), Company.is_external.is_(False))
        counts = dict(query.with_entities(Company.verification_status, func.count()).group_by(Company.verification_status).all())
        if status == "pending":
            query = query.filter(Company.verification_status.in_(["pending", "reviewing", "information_required"]))
        elif status != "all":
            query = query.filter(Company.verification_status == status)
        if search:
            query = query.filter(or_(func.lower(Company.name).contains(search.lower(), autoescape=True), func.lower(Company.nit).contains(search.lower(), autoescape=True)))
        result = query_page(query.options(joinedload(Company.owner)).order_by(Company.id.desc()), page=page, page_size=page_size)
        result["counts"] = counts
        return result
