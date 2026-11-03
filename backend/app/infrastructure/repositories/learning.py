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

    def record_integration(self, provider, now, error_code, error_text, operation):
        """Atomic upsert: concurrent first operations must not roll back a sent mail."""
        from sqlalchemy import func
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        dialect = self.session.get_bind().dialect.name
        insert = pg_insert if dialect == "postgresql" else sqlite_insert
        key, stamp = "integration:" + provider, now.isoformat() + "Z"
        table = LearningSourceSnapshot
        content = {"last_success_at": None if error_code else stamp, "error_code": error_code, "operation": operation}
        statement = insert(table).values(id=key, content=content, fetched_at=now, attempted_at=now, error=error_text)
        last_success = table.content["last_success_at"].as_string() if error_code else stamp
        json_object = func.json_build_object if dialect == "postgresql" else func.json_object
        statement = statement.on_conflict_do_update(index_elements=[table.id],
            set_={"content": json_object("last_success_at", last_success, "error_code", error_code, "operation", operation),
                  "attempted_at": now, "fetched_at": table.fetched_at if error_code else now, "error": error_text},
            where=table.attempted_at <= now)
        self.session.execute(statement)
        for row in list(self.session.identity_map.values()):
            if isinstance(row, LearningSourceSnapshot) and row.id == key:
                self.session.expire(row)

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
