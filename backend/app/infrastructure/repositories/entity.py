from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

Entity = TypeVar("Entity")


class SqlAlchemyRepository(Generic[Entity]):
    def __init__(self, session: Session, model: type[Entity]):
        self.session = session
        self.model = model

    def get(self, entity_id: int) -> Entity | None:
        return self.session.get(self.model, entity_id)

    def new(self, **values: Any) -> Entity:
        return self.model(**values)
