from types import SimpleNamespace

from app.domain.entities.enums import UserRole
from app.infrastructure.database.models import CareerCoachState, Profile, User
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class ProfileRepository(SqlAlchemyRepository[Profile]):
    def market_participants(self, family, level, demo=False):
        if not family or not level:
            return []
        choice = Profile.preferences["market_participation"]
        rows = self.session.query(Profile.user_id, Profile.skills, Profile.location, choice.label("participation"), Profile.preferences["radar_demo"].as_boolean().label("is_demo"), User.email, User.email_verified).join(User, User.id == Profile.user_id).filter(
            User.role == UserRole.CANDIDATE, User.email_verified.is_(True), choice["enabled"].as_boolean().is_(True),
            choice["family"].as_string() == family, choice["level"].as_string() == level,
            Profile.preferences["radar_demo"].as_boolean().is_(True) if demo else Profile.preferences["radar_demo"].as_boolean().is_not(True)).all()
        return [SimpleNamespace(**row._mapping) for row in rows]

    def lock_owner(self, user_id):
        self.session.query(Profile).filter_by(user_id=user_id).update({Profile.id: Profile.id}, synchronize_session=False)

    def coach_state(self, user_id):
        return self.session.get(CareerCoachState, user_id)

    def new_coach_state(self, user_id):
        return CareerCoachState(user_id=user_id, content={"writing": [], "drafts": []})
