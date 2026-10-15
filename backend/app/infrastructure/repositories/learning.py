from app.infrastructure.database.models import (
    AssessmentAttempt,
    LearningPlan,
    LearningResource,
    LearningSourceSnapshot,
)


class LearningRepository:
    def __init__(self, session):
        self.session = session

    def resources(self):
        return self.session.query(LearningResource).order_by(LearningResource.created_at.desc(), LearningResource.id).all()

    def resource(self, resource_id):
        return self.session.get(LearningResource, resource_id)

    def new_resource(self, **values):
        return LearningResource(**values)

    def source_snapshot(self, key):
        return self.session.get(LearningSourceSnapshot, key)

    def new_source_snapshot(self, **values):
        return LearningSourceSnapshot(**values)

    def trim_source_snapshots(self):
        # Keep at most 40 cached searches; persistent provider snapshots are separate.
        rows = self.session.query(LearningSourceSnapshot).filter(LearningSourceSnapshot.id.like("sena-search:%")).order_by(LearningSourceSnapshot.fetched_at.desc()).offset(39).all()
        for row in rows:
            self.session.delete(row)

    def lock_owner(self, user_id):
        from app.infrastructure.database.models import User
        self.session.query(User).filter_by(id=user_id).update({User.id: User.id}, synchronize_session=False)

    def plans(self, user_id):
        return self.session.query(LearningPlan).filter_by(user_id=user_id).order_by(LearningPlan.id.desc()).all()

    def plan(self, user_id, resource_id):
        return self.session.query(LearningPlan).filter_by(user_id=user_id, resource_id=resource_id).first()

    def new_plan(self, **values):
        return LearningPlan(**values)

    def claim_progress(self, plan_id, user_id, version):
        return self.session.query(LearningPlan).filter_by(id=plan_id, user_id=user_id, version=version).update(
            {LearningPlan.version: version + 1}, synchronize_session="fetch") == 1

    def attempts(self, user_id):
        return self.session.query(AssessmentAttempt).filter_by(user_id=user_id).order_by(AssessmentAttempt.started_at.desc()).all()

    def valid_foundations_for_users(self, user_ids, now):
        from sqlalchemy.orm import load_only
        if not user_ids:
            return []
        return self.session.query(AssessmentAttempt).options(load_only(AssessmentAttempt.user_id, AssessmentAttempt.skill, AssessmentAttempt.score, AssessmentAttempt.valid_until)).filter(AssessmentAttempt.user_id.in_(user_ids), AssessmentAttempt.passed.is_(True), AssessmentAttempt.valid_until >= now).all()

    def attempt(self, attempt_id):
        return self.session.get(AssessmentAttempt, attempt_id)

    def new_attempt(self, **values):
        return AssessmentAttempt(**values)

    def claim_submission(self, attempt_id, user_id, now):
        return self.session.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id, AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.status == "active", AssessmentAttempt.expires_at >= now).update(
                {AssessmentAttempt.status: "completed", AssessmentAttempt.submitted_at: now}, synchronize_session="fetch") == 1
