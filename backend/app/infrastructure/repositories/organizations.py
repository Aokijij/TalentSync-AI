from datetime import datetime

from sqlalchemy import update

from app.infrastructure.database.models import Company, CompanyInvitation, CompanyMember


class OrganizationRepository:
    def __init__(self, session):
        self.session = session

    def member_for_user(self, user_id):
        return self.session.query(CompanyMember).filter_by(user_id=user_id).first()

    def members(self, company_id):
        return self.session.query(CompanyMember).filter_by(company_id=company_id).all()

    def new_member(self, **values):
        return CompanyMember(**values)

    def new_invitation(self, **values):
        return CompanyInvitation(**values)

    def invitation(self, digest):
        return self.session.query(CompanyInvitation).filter_by(token_hash=digest).first()

    def consume_invitation(self, invitation_id):
        result = self.session.execute(update(CompanyInvitation).where(
            CompanyInvitation.id == invitation_id, CompanyInvitation.used_at.is_(None),
            CompanyInvitation.expires_at > datetime.utcnow(),
        ).values(used_at=datetime.utcnow()).execution_options(synchronize_session=False))
        return result.rowcount == 1

    def verification_queue(self):
        return self.session.query(Company).filter(Company.verification_required.is_(True)).order_by(Company.id.desc()).limit(200).all()
