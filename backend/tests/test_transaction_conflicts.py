import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.errors import UseCaseError
from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import User
from app.infrastructure.database.session import Base
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.parametrize("operation", ["flush", "commit"])
def test_conflicting_write_rolls_back_and_keeps_session_usable(operation):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with sessionmaker(bind=engine)() as session:
            db = SqlAlchemyUnitOfWork(session)
            db.add(User(name="Primero", email="same@example.com", password_hash="test", role=UserRole.CANDIDATE))
            db.commit()
            db.add(User(name="Segundo", email="same@example.com", password_hash="test", role=UserRole.CANDIDATE))
            with pytest.raises(UseCaseError) as error:
                getattr(db, operation)()
            assert error.value.status_code == 409
            assert session.query(User).count() == 1
            db.add(User(name="Tercero", email="other@example.com", password_hash="test", role=UserRole.CANDIDATE))
            db.commit()
            assert session.query(User).count() == 2
    finally:
        engine.dispose()
