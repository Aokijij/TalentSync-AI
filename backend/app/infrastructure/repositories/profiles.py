from app.infrastructure.database.models import Profile
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class ProfileRepository(SqlAlchemyRepository[Profile]):
    pass
