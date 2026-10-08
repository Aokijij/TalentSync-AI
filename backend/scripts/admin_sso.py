"""Local staff provisioning; never creates accounts or promotes roles."""
import argparse

from app.application.errors import UseCaseError
from app.application.use_cases.admin_sso import provision
from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def main():
    parser = argparse.ArgumentParser(description="Vincular una identidad corporativa a una cuenta administradora existente")
    parser.add_argument("action", choices=("bind", "revoke"))
    parser.add_argument("--email", required=True)
    parser.add_argument("--subject")
    parser.add_argument("--provider", choices=("workspace", "entra"), default=settings.admin_sso_provider)
    args = parser.parse_args()
    if (args.action == "bind") != bool(args.subject):
        parser.error("bind exige --subject y revoke no lo admite")
    try:
        with SessionLocal() as session:
            provision(SqlAlchemyUnitOfWork(session), args.email, args.subject, provider=args.provider)
    except UseCaseError as error:
        parser.error(error.detail)
    print("Aprovisionamiento actualizado y sesiones anteriores revocadas.")


if __name__ == "__main__":
    main()
