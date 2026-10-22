from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload, load_only, selectinload

from app.infrastructure.database.models import Application, Company, Job, OfferFeedback
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class JobRepository(SqlAlchemyRepository[Job]):
    def board_choices(self, company_id):
        count = select(func.count(Application.id)).where(Application.job_id == Job.id).correlate(Job).scalar_subquery()
        rows = self.session.query(
            Job.id, Job.company_id, Job.title, Job.status, Job.skills,
            Job.location, Job.modality, Job.sector, Job.pipeline_stages,
            Job.created_at, count.label("applications_count"),
        ).filter(Job.company_id == company_id).order_by(Job.created_at.desc(), Job.id.desc()).all()
        return [dict(row._mapping) for row in rows]

    def company_choices(self, company_id, search, offset, limit):
        query = self.session.query(Job).filter(Job.company_id == company_id, Job.status != "filled")
        if search:
            query = query.filter(Job.title.ilike(f"%{search.strip()}%"))
        total = query.count()
        count = select(func.count(Application.id)).where(Application.job_id == Job.id).correlate(Job).scalar_subquery()
        rows = query.with_entities(Job.id, Job.title, Job.status, Job.skills, count.label("applications_count")).order_by(Job.created_at.desc(), Job.id.desc()).offset(offset).limit(limit).all()
        return [dict(row._mapping) for row in rows], total
    def market_jobs(self, since, demo=False):
        query = self.session.query(Job).options(
            joinedload(Job.company).load_only(Company.name),
            # Public statistics need neither embeddings nor selection data.
            load_only(
                Job.id, Job.company_id, Job.title, Job.description, Job.source_kind, Job.source_name,
                Job.external_url, Job.status, Job.created_at, Job.expires_at, Job.sector, Job.location,
                Job.skills, Job.salary, Job.modality, Job.employment_type, Job.quality_details),
        ).filter(Job.created_at >= since)
        return (query.filter(Job.source_name == "radar-demo", Job.status == "draft") if demo else self._available(query)).all()

    def offer_feedback_for(self, job_id):
        return self.session.query(OfferFeedback).filter_by(job_id=job_id).all()

    def candidate_offer_feedback(self, user_id, job_id):
        return self.session.query(OfferFeedback).filter_by(user_id=user_id, job_id=job_id).first()

    def new_offer_feedback(self, **values):
        return OfferFeedback(**values)

    @staticmethod
    def _available(query):
        now = datetime.utcnow()
        return query.filter(
            Job.status == "active",
            or_(Job.expires_at.is_(None), Job.expires_at >= now),
        )

    def active(self) -> list[Job]:
        return self._available(self.session.query(Job)).all()

    def active_for_matching(self) -> list[Job]:
        # Trust is evaluated over all recent processes of each employer. Load
        # those relationships in batches rather than once per recommended job.
        return self._available(self.session.query(Job).options(
            joinedload(Job.company).selectinload(Company.jobs).selectinload(Job.applications),
            joinedload(Job.company).selectinload(Company.incidents),
        )).all()

    def count_active(self) -> int:
        return self._available(self.session.query(Job)).count()

    def active_skill_rows(self) -> list[tuple[list[str]]]:
        return self._available(self.session.query(Job.skills)).all()

    def active_external(self) -> list[Job]:
        return self._available(
            self.session.query(Job).filter(Job.source_kind == "external")
        ).all()

    def external_listings(self) -> list[Job]:
        return (
            self.session.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.source_kind == "external")
            .order_by(Job.created_at.desc(), Job.id.desc())
            .all()
        )

    def company_attention_jobs(self, created_before: datetime) -> list[Job]:
        return (
            self._available(
                self.session.query(Job)
                .options(joinedload(Job.company), selectinload(Job.applications))
                .filter(
                    Job.source_kind == "internal",
                    Job.created_at <= created_before,
                )
            )
            .all()
        )

    def get_with_company(self, job_id: int) -> Job | None:
        return (
            self.session.query(Job)
            .options(joinedload(Job.company))
            .filter(Job.id == job_id)
            .first()
        )

    def find_external(self, source_name: str, external_id: str) -> Job | None:
        return (
            self.session.query(Job)
            .filter(Job.source_name == source_name, Job.external_id == external_id)
            .first()
        )

    def find_external_listing(
        self,
        source_name: str,
        company_id: int,
        title: str,
        location: str | None,
    ) -> Job | None:
        query = self.session.query(Job).filter(
            Job.source_name == source_name,
            Job.company_id == company_id,
            Job.title == title,
        )
        if location:
            query = query.filter(Job.location == location)
        else:
            query = query.filter(Job.location.is_(None))
        return query.order_by(Job.created_at.desc()).first()

    def count(self) -> int:
        return self.session.query(Job).count()

    @staticmethod
    def _scope(query, scope: str):
        if scope == "platform":
            return query.filter(Job.source_kind == "internal")
        if scope == "external":
            return query.filter(Job.source_kind == "external")
        return query

    def admin_page(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        scope: str = "platform",
    ) -> tuple[list[Job], int]:
        query = self._scope(
            self.session.query(Job).options(
                joinedload(Job.company), selectinload(Job.applications)
            ),
            scope,
        )
        if search:
            pattern = f"%{search.strip()}%"
            query = query.join(Job.company).filter(
                or_(
                    Job.title.ilike(pattern),
                    Job.description.ilike(pattern),
                    Company.name.ilike(pattern),
                )
            )
        total = query.count()
        return (
            query.order_by(Job.created_at.desc(), Job.id.desc())
            .offset(offset)
            .limit(limit)
            .all(),
            total,
        )

    def count_by_scope(self, scope: str) -> int:
        return self._scope(self.session.query(Job), scope).count()

    def search(
        self,
        search: str | None,
        modality: str | None,
        location: str | None,
        department: str | None,
        sector: str | None,
        employment_type: str | None,
        status_filter: str | None,
        min_salary: float | None = None,
        max_salary: float | None = None,
        created_after: datetime | None = None,
        sort: str = "newest",
    ) -> list[Job]:
        query = self.session.query(Job).options(
            joinedload(Job.company).selectinload(Company.jobs).selectinload(Job.applications),
            joinedload(Job.company).selectinload(Company.incidents),
            selectinload(Job.applications),
        )
        if status_filter:
            query = query.filter(Job.status == status_filter)
            if status_filter == "active":
                query = query.filter(
                    or_(Job.expires_at.is_(None), Job.expires_at >= datetime.utcnow())
                )
        if modality:
            query = query.filter(Job.modality == modality)
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))
        if department:
            query = query.filter(Job.department == department)
        if sector:
            query = query.filter(Job.sector == sector)
        if employment_type:
            query = query.filter(Job.employment_type == employment_type)
        if min_salary is not None:
            query = query.filter(Job.salary >= min_salary)
        if max_salary is not None:
            query = query.filter(Job.salary <= max_salary)
        if created_after is not None:
            query = query.filter(Job.created_at >= created_after)
        if search:
            query = query.filter(
                Job.title.ilike(f"%{search}%")
                | Job.description.ilike(f"%{search}%")
                | Job.requirements.ilike(f"%{search}%")
            )
        if sort == "salary_desc":
            return query.order_by(Job.salary.desc().nullslast(), Job.created_at.desc()).all()
        if sort == "salary_asc":
            return query.order_by(Job.salary.asc().nullslast(), Job.created_at.desc()).all()
        if sort == "oldest":
            return query.order_by(Job.created_at.asc()).all()
        return query.order_by(Job.created_at.desc()).all()
