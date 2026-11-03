from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(
    settings.database_url, connect_args=connect_args, pool_pre_ping=True
)

def configure_sqlite(connection, _):
    # Readers must not block session revocation or short writes while a
    # dashboard/model request is traversing the recruitment dataset.
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


if engine.dialect.name == "sqlite" and engine.url.database not in {None, "", ":memory:"}:
    event.listen(engine, "connect", configure_sqlite)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
