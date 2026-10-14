from app.infrastructure.database.models import CareerCoachState, Profile
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class ProfileRepository(SqlAlchemyRepository[Profile]):
    def lock_owner(self, user_id):
        self.session.query(Profile).filter_by(user_id=user_id).update({Profile.id: Profile.id}, synchronize_session=False)

    def coach_state(self, user_id):
        return self.session.get(CareerCoachState, user_id)

    def new_coach_state(self, user_id):
        return CareerCoachState(user_id=user_id, content={"writing": [], "drafts": []})
