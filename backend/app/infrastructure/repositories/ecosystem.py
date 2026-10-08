from app.infrastructure.database.models import ModelAuditRun, TrustIncident


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

    def new_audit(self, **values):
        return ModelAuditRun(**values)

    def audits(self):
        return self.session.query(ModelAuditRun).order_by(ModelAuditRun.id.desc()).limit(20).all()
