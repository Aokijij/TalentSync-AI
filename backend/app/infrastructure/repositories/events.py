from app.infrastructure.database.models import EventLog
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class EventRepository(SqlAlchemyRepository[EventLog]):
    def for_entity(self, entity_type: str, entity_id: int, limit: int = 100) -> list[EventLog]:
        return (
            self.session.query(EventLog)
            .filter(EventLog.entity_type == entity_type, EventLog.entity_id == entity_id)
            .order_by(EventLog.created_at.desc(), EventLog.id.desc())
            .limit(min(max(limit, 1), 500))
            .all()
        )
