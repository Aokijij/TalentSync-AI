from app.infrastructure.database.models import ModelExperiment, RecommendationFeedback


class PersonalizationRepository:
    def __init__(self, session):
        self.session = session

    def feedback(self, user_id=None):
        query = self.session.query(RecommendationFeedback)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.order_by(RecommendationFeedback.updated_at.desc()).limit(5000).all()

    def find(self, user_id, job_id):
        return self.session.query(RecommendationFeedback).filter_by(user_id=user_id, job_id=job_id).first()

    def new_feedback(self, **values):
        return RecommendationFeedback(**values)

    def purge_user(self, user_id):
        self.session.query(RecommendationFeedback).filter_by(user_id=user_id).delete(synchronize_session="fetch")
        # A conservative withdrawal also removes any aggregate learned artifact.
        self.invalidate_artifacts("invalidated_consent_withdrawal")

    def invalidate_artifacts(self, reason):
        for row in self.session.query(ModelExperiment).all():
            if row.artifact:
                row.artifact = {}
                row.status = reason

    def experiments(self):
        return self.session.query(ModelExperiment).order_by(ModelExperiment.id.desc()).limit(20).all()

    def new_experiment(self, **values):
        return ModelExperiment(**values)
