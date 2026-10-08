from app.infrastructure.database.models import AssessmentAttempt, LearningPlan


class LearningRepository:
    def __init__(self, session):
        self.session = session

    def plans(self, user_id):
        return self.session.query(LearningPlan).filter_by(user_id=user_id).order_by(LearningPlan.id.desc()).all()

    def plan(self, user_id, resource_id):
        return self.session.query(LearningPlan).filter_by(user_id=user_id, resource_id=resource_id).first()

    def new_plan(self, **values):
        return LearningPlan(**values)

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
