from sqlalchemy import case, func, or_

from app.infrastructure.database.models import (
    Application,
    Company,
    Job,
    ModelAuditRun,
    TrustIncident,
)


class EcosystemRepository:
    def __init__(self, session):
        self.session = session

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
