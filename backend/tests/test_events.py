
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application.use_cases.events import record_event
from app.infrastructure.database.session import Base
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_events_share_transaction_and_reject_sensitive_payloads():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        db = SqlAlchemyUnitOfWork(session)
        record_event(db, "application.created", "application", 7, details={"job_id": 3})
        session.flush()
        assert db.events.for_entity("application", 7)[0].details == {"job_id": 3}
        session.rollback()
        assert db.events.for_entity("application", 7) == []
        with pytest.raises(ValueError, match="Unsupported"):
            record_event(db, "account.created", "user", 1, details={"password": "secret"})
        with pytest.raises(ValueError, match="scalar"):
            record_event(db, "account.created", "user", 1, details={"source": {"token": "secret"}})
    engine.dispose()
