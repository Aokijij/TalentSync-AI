# ruff: noqa: F811
from types import SimpleNamespace as Row

from test_api_flows import client, company_account, create_job, register  # noqa: F401
from test_ecosystem import administrator

from app.domain.services.academic_matching import education_evaluation
from app.infrastructure.database.models import Application, Job


def test_board_choices_only_include_own_jobs_and_no_nlp_or_unneeded_profile_data(client):
    _, company = company_account(client, "board-owner")
    _, outsider = company_account(client, "board-outsider")
    own = create_job(client, company)
    other = create_job(client, outsider)
    # Filled jobs must remain available to consult their selection history.
    with client.session_factory() as db:
        db.get(Job, own["id"]).status = "filled"
        db.commit()
    response = client.get("/api/v1/jobs/mine/board", headers=company)
    assert response.status_code == 200, response.text
    assert [job["id"] for job in response.json()] == [own["id"]]
    assert other["id"] != own["id"] and response.json()[0]["status"] == "filled"
    assert "embedding" not in response.text and "description" not in response.json()[0]
    assert response.json()[0]["pipeline_stages"] is not None
    _, candidate = register(client, "board-no-company-access")
    assert client.get("/api/v1/jobs/mine/board", headers=candidate).status_code == 403


def test_board_returns_real_counts_and_sector_for_each_own_vacancy_including_completed_processes(client):
    _, company = company_account(client, "board-counts-owner")
    _, outsider = company_account(client, "board-counts-outsider")
    jobs = [create_job(client, company) for _ in range(3)]
    other = create_job(client, outsider)
    first, _ = register(client, "board-counts-first")
    second, _ = register(client, "board-counts-second")
    with client.session_factory() as db:
        db.add_all([
            Application(job_id=jobs[0]["id"], user_id=first["id"], status="submitted"),
            Application(job_id=jobs[0]["id"], user_id=second["id"], status="hired"),
            Application(job_id=jobs[1]["id"], user_id=first["id"], status="rejected"),
            Application(job_id=other["id"], user_id=second["id"], status="submitted"),
        ])
        db.get(Job, jobs[1]["id"]).status = "filled"
        db.commit()
    response = client.get("/api/v1/jobs/mine/board", headers=company)
    assert response.status_code == 200, response.text
    rows = {row["id"]: row for row in response.json()}
    assert set(rows) == {job["id"] for job in jobs}
    assert [rows[job["id"]]["applications_count"] for job in jobs] == [2, 1, 0]
    assert all(rows[job["id"]]["sector"] == job["sector"] for job in jobs)
    assert rows[jobs[1]["id"]]["status"] == "filled"


def test_logistics_administration_is_recognized_and_compared_automatically_without_inventing_equivalence():
    target = Row(required_study_fields=["Administración logística"], required_education_level="university", quality_details={})
    systems = Row(educations=[{"degree": "Ingeniería de Sistemas", "level": "university"}])
    result = education_evaluation(systems, target)
    assert result["selected"]["status"] == "unrelated" and result["status"] == "not_met"
    graduate = Row(educations=[{"degree": "Administradora logística", "level": "university"}])
    assert education_evaluation(graduate, target)["status"] == "fulfilled"
    technician = Row(educations=[{"degree": "Técnica en gestión logística", "level": "technical"}])
    assert education_evaluation(technician, target)["status"] == "partial"


def test_learning_demand_counts_vacancies_once_and_does_not_expose_candidates(client):
    admin = administrator(client)
    _, company = company_account(client, "demand-owner")
    create_job(client, company)
    _, candidate = register(client, "demand-private")
    assert client.get("/api/v1/admin/learning/demand", headers=candidate).status_code == 403
    response = client.get("/api/v1/admin/learning/demand", headers=admin)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["vacancy_sample"] == 1
    assert result["skills"] and all(row["vacancies"] == 1 and row["companies"] == 1 for row in result["skills"])
    assert "demand-private" not in response.text and "user_id" not in response.text
    assert all(row["resources"] >= row["published_resources"] for row in result["skills"])


def test_official_opportunity_sources_cover_other_cities_and_do_not_claim_open_enrollment(client):
    _, candidate = register(client, "opportunity-candidate")
    response = client.get("/api/v1/learning/opportunity-sources", headers=candidate)
    assert response.status_code == 200, response.text
    sources = response.json()["sources"]
    assert {"Medellín", "Bogotá", "Barranquilla", "Toda Colombia"} <= {row["city"] for row in sources}
    assert all(row["url"].startswith("https://") and "status" not in row for row in sources)
    assert "no confirma" in response.json()["notice"]
