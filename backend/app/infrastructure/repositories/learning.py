from app.infrastructure.database.models import (
    AssessmentAttempt,
    LearningPlan,
    LearningResource,
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

    def attempt(self, attempt_id):
        return self.session.get(AssessmentAttempt, attempt_id)

    def new_attempt(self, **values):
        return AssessmentAttempt(**values)

    def claim_submission(self, attempt_id, user_id, now):
        return self.session.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id, AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.status == "active", AssessmentAttempt.expires_at >= now).update(
                {AssessmentAttempt.status: "completed", AssessmentAttempt.submitted_at: now}, synchronize_session="fetch") == 1
