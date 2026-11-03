"""Publish reviewed official courses only in the owned development SQLite database."""
import json
from pathlib import Path

from app.application.use_cases.learning_resources import import_source
from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.infrastructure import curated_learning
from app.infrastructure.database.models import User
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[2]


def main():
    expected = f"sqlite:///{(ROOT / '.local/talentsync.sqlite3').as_posix()}"
    if settings.environment != "development" or settings.database_url != expected:
        raise SystemExit("La biblioteca de revisión requiere la base SQLite local aislada.")
    catalog = curated_learning.catalog()
    with SessionLocal() as session:
        admin = session.query(User).filter_by(role=UserRole.ADMIN).order_by(User.id).first()
        if admin is None:
            raise SystemExit("Crea primero las cuentas locales de revisión.")
        result = import_source(SqlAlchemyUnitOfWork(session), admin, catalog["resources"], namespace="curated", publish=True)
    report = {"catalog_revision": catalog["revision"], "reviewed_at": catalog["reviewed_at"],
              "resources": len(catalog["resources"]), "providers": len(catalog["providers"]),
              "created": result["created"], "preserved": result["existing"],
              "free": sum(row["content"]["cost"] == "free" for row in catalog["resources"]),
              "paid": sum(row["content"]["cost"] == "paid" for row in catalog["resources"])}
    target = ROOT / ".local/verification/education-catalog.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
