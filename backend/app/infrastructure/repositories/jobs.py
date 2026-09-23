from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.infrastructure.database.models import Job
from app.infrastructure.repositories.entity import SqlAlchemyRepository


class JobRepository(SqlAlchemyRepository[Job]):
    @staticmethod
    def _available(query):
        now = datetime.utcnow()
        return query.filter(
            Job.status == "active",
            or_(Job.expires_at.is_(None), Job.expires_at >= now),
        )

    def active(self) -> list[Job]:
        return self._available(self.session.query(Job)).all()

    def count_active(self) -> int:
        return self._available(self.session.query(Job)).count()

    def active_skill_rows(self) -> list[tuple[list[str]]]:
        return self._available(self.session.query(Job.skills)).all()

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

    def count(self) -> int:
        return self.session.query(Job).count()

    def recent(self) -> list[Job]:
        return self.session.query(Job).order_by(Job.created_at.desc()).limit(50).all()

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
        query = self.session.query(Job).options(joinedload(Job.company))
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
