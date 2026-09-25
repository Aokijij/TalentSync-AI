from datetime import datetime

from app.domain.entities.job_sectors import JOB_SECTORS
from app.scripts.seed_demo_catalog import build_demo_catalog


def test_demo_catalog_has_twenty_companies_and_eight_to_fourteen_jobs_each():
    catalog = build_demo_catalog(datetime(2026, 9, 25, 12, 0, 0))

    assert len(catalog) == 20
    assert all(8 <= len(company["jobs"]) <= 14 for company in catalog)
    assert sum(len(company["jobs"]) for company in catalog) == 217
    assert all(company["sector"] in JOB_SECTORS for company in catalog)


def test_demo_vacancies_are_honest_functional_and_unique():
    catalog = build_demo_catalog(datetime(2026, 9, 25, 12, 0, 0))
    jobs = [job for company in catalog for job in company["jobs"]]

    assert len({job["external_id"] for job in jobs}) == len(jobs)
    assert all(len(job["skills"]) >= 3 for job in jobs)
    assert all("vacante demostrativa" in job["description"].lower() for job in jobs)
    assert all(job["application_questions"] for job in jobs)
