from typing import Any, Protocol, TypeVar

Entity = TypeVar("Entity", covariant=True)


class EntityRepository(Protocol[Entity]):
    def get(self, entity_id: int) -> Entity | None: ...
    def new(self, **values: Any) -> Entity: ...
