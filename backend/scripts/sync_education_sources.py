"""Refresh approved SENA metadata and Sapiencia calls in the owned local SQLite."""
import json
from pathlib import Path

from app.application.errors import UseCaseError
from app.application.use_cases import learning_sources
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.public_learning import PublicLearningCatalog

ROOT = Path(__file__).resolve().parents[2]


def main():
    expected = f"sqlite:///{(ROOT / '.local/talentsync.sqlite3').as_posix()}"
    if settings.environment != "development" or settings.database_url != expected:
        raise SystemExit("La actualización requiere la SQLite local aislada.")
    gateway = PublicLearningCatalog()
    with SessionLocal() as session:
        admin = session.query(User).filter_by(role=UserRole.ADMIN).order_by(User.id).first()
        if admin is None:
            raise SystemExit("Prepara primero los accesos locales de revisión.")
        db = SqlAlchemyUnitOfWork(session)
        sena = learning_sources.refresh_sena(db, admin, gateway, limit=40, budget_seconds=120)
        try:
            sapiencia = learning_sources.refresh_sapiencia(db, admin, gateway)
            report = {"sena": sena, "sapiencia": {"calls": len(sapiencia["items"]), "warning": sapiencia["warning"]}}
        except UseCaseError as error:
            report = {"sena": sena, "sapiencia": {"calls": 0, "warning": error.detail}}
    target = ROOT / ".local/verification/education-sources.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
