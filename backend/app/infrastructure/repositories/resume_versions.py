from app.infrastructure.database.models import ResumeVersion


class ResumeVersionRepository:
    def __init__(self, session):
        self.session = session

    def get(self, version_id):
        return self.session.get(ResumeVersion, version_id)

    def find_request(self, user_id, request_key):
        return self.session.query(ResumeVersion).filter_by(user_id=user_id, request_key=request_key).first()

    def for_job(self, user_id, job_id):
        return self.session.query(ResumeVersion).filter_by(user_id=user_id, job_id=job_id).order_by(ResumeVersion.created_at.desc(), ResumeVersion.id.desc()).limit(31).all()

    def count_for_job(self, user_id, job_id):
        return self.session.query(ResumeVersion).filter_by(user_id=user_id, job_id=job_id).filter(ResumeVersion.snapshot["kind"].as_string().is_distinct_from("profile")).count()

    def new(self, **values):
        return ResumeVersion(**values)
