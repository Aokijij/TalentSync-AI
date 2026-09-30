"""Remove obsolete Jooble catalog records after migration to richer providers."""

import json

from app.infrastructure.database.models import Company, Job
from app.infrastructure.database.session import SessionLocal


def cleanup() -> dict[str, int]:
    with SessionLocal() as session:
        jobs = (
            session.query(Job)
            .filter(Job.source_kind == "external", Job.source_name == "Jooble")
            .all()
        )
        company_ids = {job.company_id for job in jobs}
        for job in jobs:
            session.delete(job)
        session.flush()
        companies_removed = 0
        for company_id in company_ids:
            company = session.get(Company, company_id)
            remaining = session.query(Job).filter(Job.company_id == company_id).count()
            if company is not None and company.is_external and remaining == 0:
                session.delete(company)
                companies_removed += 1
        session.commit()
        return {"jobs_removed": len(jobs), "companies_removed": companies_removed}


if __name__ == "__main__":
    print(json.dumps(cleanup(), ensure_ascii=False))
