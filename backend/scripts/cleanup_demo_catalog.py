"""Remove the old public demonstration catalog without touching real imports."""

import json

from app.infrastructure.database.models import Company, Job
from app.infrastructure.database.session import SessionLocal

DEMO_SOURCE = "TalentSync Demo"


def cleanup_demo_catalog() -> dict[str, int]:
    with SessionLocal() as session:
        jobs = session.query(Job).filter(Job.source_kind == "demo").all()
        company_ids = {job.company_id for job in jobs}
        for job in jobs:
            session.delete(job)
        session.flush()
        companies = (
            session.query(Company)
            .filter(
                Company.source_name == DEMO_SOURCE,
                Company.id.in_(company_ids) if company_ids else False,
            )
            .all()
        )
        for company in companies:
            session.delete(company)
        session.commit()
        return {"jobs_removed": len(jobs), "companies_removed": len(companies)}


if __name__ == "__main__":
    print(json.dumps(cleanup_demo_catalog(), ensure_ascii=False))
