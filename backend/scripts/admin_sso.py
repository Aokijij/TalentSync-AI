"""Local staff provisioning; never creates accounts or promotes roles."""
import argparse

from app.application.errors import UseCaseError
from app.application.use_cases.admin_sso import provision
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def main():
    parser = argparse.ArgumentParser(description="Vincular un sujeto Google Workspace a una cuenta administradora existente")
    parser.add_argument("action", choices=("bind", "revoke"))
    parser.add_argument("--email", required=True)
    parser.add_argument("--subject")
    args = parser.parse_args()
    if (args.action == "bind") != bool(args.subject):
        parser.error("bind exige --subject y revoke no lo admite")
    try:
        with SessionLocal() as session:
            provision(SqlAlchemyUnitOfWork(session), args.email, args.subject)
    except UseCaseError as error:
        parser.error(error.detail)
    print("Aprovisionamiento actualizado y sesiones anteriores revocadas.")


if __name__ == "__main__":
    main()
