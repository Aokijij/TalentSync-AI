from app.domain.entities.enums import UserRole


def requires_mfa_setup(role, company_mfa_required=True):
    return role == UserRole.ADMIN or role == UserRole.COMPANY and company_mfa_required
