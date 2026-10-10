from datetime import datetime, timedelta

from sqlalchemy import and_, case, func, or_

from app.infrastructure.database.models import (
    Application,
    Company,
    Job,
    ModelAuditRun,
    TrustIncident,
)
from app.infrastructure.repositories.paging import query_page


class EcosystemRepository:
    def __init__(self, session):
        self.session = session

    def company_directory(self, *, search, filter, page, page_size):
        cutoff = datetime.utcnow() - timedelta(days=90)
        processes = self.session.query(Job.company_id.label("company_id"), func.count(Application.id).label("measured"),
            func.sum(case((Application.resolution_reason == "response_deadline", 1), else_=0)).label("missed")).join(Application, Application.job_id == Job.id).filter(
                Application.created_at >= cutoff, or_(Application.first_response_at.is_not(None), Application.resolution_reason == "response_deadline")).group_by(Job.company_id).subquery()
        incidents = self.session.query(TrustIncident.company_id.label("company_id"), func.count(TrustIncident.id).label("confirmed")).filter(
            TrustIncident.created_at >= cutoff, TrustIncident.status.in_(["confirmed", "appealed"])).group_by(TrustIncident.company_id).subquery()
        measured = func.coalesce(processes.c.measured, 0)
        missed = func.coalesce(processes.c.missed, 0)
        confirmed = func.coalesce(incidents.c.confirmed, 0)
        raw_score = 100.0 * (measured - missed + 5) / (measured + 5) - case((confirmed >= 4, 40), else_=confirmed * 10)
        score = func.round(case((raw_score < 0, 0), else_=raw_score), 1)
        rated = or_(measured > 0, confirmed > 0)
        reduced = or_(and_(measured >= 5, score < 60), confirmed >= 2)
        query = self.session.query(Company.id, Company.name, measured.label("measured"), missed.label("missed"), confirmed.label("confirmed")).outerjoin(
            processes, processes.c.company_id == Company.id).outerjoin(incidents, incidents.c.company_id == Company.id).filter(Company.is_external.is_(False))
        organization_count = query.count()
        if search:
            query = query.filter(func.lower(Company.name).contains(search.lower(), autoescape=True))
        if filter == "attention":
            query = query.filter(or_(reduced, confirmed > 0, missed > 0))
        elif filter == "rated":
            query = query.filter(rated)
        elif filter == "unrated":
            query = query.filter(~rated)
        result = query_page(query.order_by(reduced.desc(), func.lower(Company.name), Company.id), page=page, page_size=page_size)
        result["items"] = [row._asdict() for row in result["items"]]
        result["organization_count"] = organization_count
        return result

    def new_incident(self, **values):
        return TrustIncident(**values)

    def incident(self, incident_id):
        return self.session.get(TrustIncident, incident_id)

    def incidents(self, *, company_id=None, reporter_id=None):
        query = self.session.query(TrustIncident)
        if company_id is not None:
            query = query.filter_by(company_id=company_id)
        if reporter_id is not None:
            query = query.filter_by(reporter_user_id=reporter_id)
        return query.order_by(TrustIncident.id.desc()).limit(200).all()

    def incident_queue(self, *, bucket, status, category, search, sort, page, page_size):
        counts = dict(self.session.query(TrustIncident.status, func.count(TrustIncident.id)).group_by(TrustIncident.status).all())
        query = self.session.query(TrustIncident.id, TrustIncident.category, TrustIncident.status,
            TrustIncident.created_at, TrustIncident.updated_at, Company.name.label("company_name"), Job.title.label("job_title"))
        query = query.join(Company, TrustIncident.company_id == Company.id).outerjoin(Application, TrustIncident.application_id == Application.id).outerjoin(Job, Application.job_id == Job.id)
        if bucket == "pending":
            query = query.filter(TrustIncident.status.in_(["open", "in_review", "appealed"]))
        elif bucket == "resolved":
            query = query.filter(TrustIncident.status.in_(["confirmed", "dismissed"]))
        if status != "all":
            query = query.filter(TrustIncident.status == status)
        if category != "all":
            query = query.filter(TrustIncident.category == category)
        if search:
            terms = [func.lower(Company.name).contains(search.lower(), autoescape=True), func.lower(Job.title).contains(search.lower(), autoescape=True)]
            identifier = search.lstrip("#")
            if identifier.isascii() and identifier.isdigit() and len(identifier) <= 18:
                terms.append(TrustIncident.id == int(identifier))
            query = query.filter(or_(*terms))
        total = query.count()
        page = min(page, max(1, (total + page_size - 1) // page_size))
        if sort == "priority":
            query = query.order_by(case((TrustIncident.status == "appealed", 0), (TrustIncident.status == "open", 1), (TrustIncident.status == "in_review", 2), else_=3), TrustIncident.created_at.asc(), TrustIncident.id.asc())
        elif sort == "oldest":
            query = query.order_by(TrustIncident.created_at.asc(), TrustIncident.id.asc())
        else:
            query = query.order_by(TrustIncident.created_at.desc(), TrustIncident.id.desc())
        return {"items": [row._asdict() for row in query.offset((page - 1) * page_size).limit(page_size).all()],
                "total": total, "page": page, "page_size": page_size, "counts": counts}

    def new_audit(self, **values):
        return ModelAuditRun(**values)

    def audits(self):
        return self.session.query(ModelAuditRun).order_by(ModelAuditRun.id.desc()).limit(20).all()
