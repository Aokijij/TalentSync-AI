from datetime import datetime

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import joinedload

from app.domain.entities.enums import ApplicationStatus
from app.infrastructure.database.models import (
    Application,
    Job,
    Profile,
    Recommendation,
    User,
)
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class ApplicationRepository(SqlAlchemyRepository[Application]):
    def workspace_page(self, job, *, bucket="inbox", search="", score_filter="all", order="score", stage=None, interview_state="all", page=1, page_size=25):
        first_stage = (job.pipeline_stages or [{"id": "submitted"}])[0]["id"]
        final = or_(Application.released_at.is_not(None), Application.status.in_([ApplicationStatus.REJECTED, ApplicationStatus.ACCEPTED, ApplicationStatus.HIRED]))
        incoming = Application.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.SEEN])
        bucket_expr = case((final, "closed"), (incoming, "inbox"), else_="active")
        stage_expr = case((Application.status.in_([ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED]), "hired"),
            (Application.status == ApplicationStatus.REJECTED, "rejected"), else_=func.coalesce(Application.pipeline_stage, case(
            (Application.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.SEEN]), first_stage),
            (Application.status.in_([ApplicationStatus.TECHNICAL_INTERVIEW, ApplicationStatus.PSYCHOMETRIC_TEST]), "interview"),
            (Application.status.in_([ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED]), "hired"),
            (Application.status == ApplicationStatus.REJECTED, "rejected"), else_="reviewing")))
        raw_score = Recommendation.match_percentage + func.coalesce(Application.screening_adjustment, 0)
        score = case((Recommendation.id.is_(None), None), (raw_score > 100, 100.0), (raw_score < 0, 0.0), else_=raw_score)
        base = self.session.query(Application).filter(Application.job_id == job.id)
        counts = {name: amount for name, amount in base.with_entities(bucket_expr, func.count(Application.id)).group_by(bucket_expr).all()}
        stage_counts = dict(base.filter(bucket_expr == "active").with_entities(stage_expr, func.count(Application.id)).group_by(stage_expr).all())
        all_stage_counts = dict(base.with_entities(stage_expr, func.count(Application.id)).group_by(stage_expr).all())
        hired_count = base.filter(Application.status.in_([ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED])).count()
        unreviewed = base.filter(bucket_expr == "inbox", Application.reviewed_at.is_(None)).count()
        query = base.join(User, User.id == Application.user_id).outerjoin(Profile, Profile.user_id == Application.user_id).outerjoin(
            Recommendation, and_(Recommendation.user_id == Application.user_id, Recommendation.job_id == Application.job_id))
        now = datetime.utcnow()
        interview_filter = and_(~final, Application.interview_at.is_not(None), or_(Application.status.in_([ApplicationStatus.TECHNICAL_INTERVIEW, ApplicationStatus.PSYCHOMETRIC_TEST]), Application.interview_completed_at.is_(None)))
        interview_states = {
            "scheduled": and_(Application.interview_completed_at.is_(None), Application.interview_at > now),
            "unconfirmed": and_(Application.interview_completed_at.is_(None), Application.interview_at <= now),
            "awaiting_response": Application.interview_completed_at.is_not(None),
        }
        counts["interviews"] = base.filter(interview_filter).count()
        interview_counts = {key: base.filter(interview_filter, expression).count() for key, expression in interview_states.items()}
        query = query.filter(interview_filter if bucket == "interviews" else bucket_expr == bucket)
        if bucket == "interviews" and interview_state in interview_states:
            query = query.filter(interview_states[interview_state])
        if search.strip():
            term = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.filter(or_(User.name.ilike(f"%{term}%", escape="\\"), Profile.profession.ilike(f"%{term}%", escape="\\")))
        if score_filter == "strong":
            query = query.filter(score >= 85)
        elif score_filter == "missing":
            query = query.filter(score.is_(None))
        elif score_filter == "unreviewed":
            query = query.filter(Application.reviewed_at.is_(None))
        if stage:
            query = query.filter(stage_expr == stage)
        total = query.count()
        safe_page = min(page, max(1, (total + page_size - 1) // page_size))
        sorting = [score.is_(None), score.desc(), Application.created_at.asc(), Application.id.asc()] if order == "score" else [Application.created_at.desc(), Application.id.desc()] if order == "recent" else [Application.created_at.asc(), Application.id.asc()]
        rows = query.with_entities(Application.id, Application.user_id, Application.job_id, Application.status, Application.pipeline_stage,
            Application.created_at, Application.reviewed_at, Application.interview_at, Application.interview_details, Application.interview_completed_at, Application.released_at, Application.version, Application.screening_adjustment,
            User.name.label("candidate_name"), Profile.profession, Recommendation.match_percentage.label("base_match_percentage"), score.label("adjusted_match_percentage"),
            stage_expr.label("effective_stage")).order_by(*sorting).offset((safe_page - 1) * page_size).limit(page_size).all()
        return {"items": [dict(row._mapping) for row in rows], "total": total, "page": safe_page, "page_size": page_size,
                "counts": {name: counts.get(name, 0) for name in ("inbox", "active", "closed", "interviews")}, "interview_counts": interview_counts, "unreviewed": unreviewed, "stage_counts": stage_counts, "all_stage_counts": all_stage_counts, "hired_count": hired_count}

    def approaching_deadlines(self, before):
        return self.session.query(Application).filter(Application.response_due_at <= before, Application.released_at.is_(None),
            Application.status.notin_([ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED])).order_by(Application.response_due_at).limit(500).all()

    def claim_deadline(self, row, now):
        return self.session.query(Application).filter(Application.id == row.id, Application.version == row.version,
            Application.response_due_at <= now, Application.released_at.is_(None),
            Application.status.notin_([ApplicationStatus.HIRED, ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED])).update({
                Application.released_at: now, Application.status: ApplicationStatus.REJECTED,
                Application.resolution_reason: "response_deadline", Application.response_due_at: None,
                Application.version: Application.version + 1}, synchronize_session="fetch") == 1

    def count(self) -> int:
        return self.session.query(Application).count()

    def creation_dates(self) -> list[datetime]:
        return [
            created_at
            for (created_at,) in self.session.query(Application.created_at).all()
        ]

    def status_rows(self) -> list[tuple[ApplicationStatus]]:
        return self.session.query(Application.status).all()

    def count_recommended(self) -> int:
        return (
            self.session.query(Application)
            .join(
                Recommendation,
                and_(
                    Recommendation.user_id == Application.user_id,
                    Recommendation.job_id == Application.job_id,
                ),
            )
            .count()
        )

    def find_for_user_job(self, user_id: int, job_id: int) -> Application | None:
        return (
            self.session.query(Application)
            .filter(Application.user_id == user_id, Application.job_id == job_id)
            .first()
        )

    def for_user(self, user_id: int) -> list[Application]:
        return (
            self.session.query(Application)
            .filter(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
            .all()
        )

    def for_job(self, job_id: int) -> list[Application]:
        return (
            self.session.query(Application)
            .options(joinedload(Application.user))
            .filter(Application.job_id == job_id)
            .all()
        )

    def mark_submitted_seen(self, job_id: int) -> int:
        return (
            self.session.query(Application)
            .filter(
                Application.job_id == job_id,
                Application.status == ApplicationStatus.SUBMITTED,
            )
            .update(
                {Application.status: ApplicationStatus.SEEN}, synchronize_session=False
            )
        )

    def find_for_candidate_company(
        self, candidate_id: int, company_id: int
    ) -> Application | None:
        return (
            self.session.query(Application)
            .join(Job, Application.job_id == Job.id)
            .filter(Application.user_id == candidate_id, Job.company_id == company_id)
            .first()
        )

    def candidate_ids(self, job_id: int) -> list[tuple[int]]:
        return (
            self.session.query(Application.user_id)
            .filter(Application.job_id == job_id)
            .all()
        )
