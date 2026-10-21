# ruff: noqa: F811
import json
from datetime import datetime, timedelta
from types import SimpleNamespace as Row

import pytest
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.domain.services.market_radar import (
    market_report,
    peer_report,
    salary_report,
    selected_jobs,
)
from app.infrastructure.database.models import Profile, User

NOW = datetime(2026, 10, 14)
FILTERS = {"family": "software", "level": "junior", "location": "Medellín", "sector": "", "modality": "", "search": ""}


def own():
    return Row(user_id=1, skills=["python"], desired_salary=3_000_000, preferences={})


def peer(index, **changes):
    values = dict(user_id=index + 2, skills=["python", "TypeScript"] if index < 15 else ["SQL"], email=f"person{index}@workmail.co", email_verified=True, location="Medellín",
                  participation={"enabled": True, "confirmed_real": True, "family": "software", "level": "junior", "updated_at": NOW.isoformat() + "Z"})
    values.update(changes); return Row(**values)


def job(index, **changes):
    values = dict(id=index, company_id=index, company_name=f"Empresa {index}", title="Desarrollador Python", description="Desarrollo de servicios web", source_kind="internal", source_name=None,
                  external_url=None, status="active", created_at=NOW - timedelta(days=2), expires_at=None, sector="Tecnología y software", location="Medellín", skills=["python", "SQL"],
                  salary=2_000_000 + index * 100_000, modality="onsite", employment_type="full_time", quality_details={"seniority": "junior", "salary_currency": "COP", "salary_period": "monthly", "salary_basis": "gross_base", "weekly_hours": 40, "contract_type": "indefinite"})
    values.update(changes); return Row(**values)


def test_peers_are_opt_in_and_small_groups_never_disclose_counts():
    result = peer_report(own(), [peer(i) for i in range(19)], FILTERS, NOW)
    assert result["status"] == "insufficient_data" and "sample" not in result and not result["skills"]
    result = peer_report(own(), [peer(i) for i in range(20)], FILTERS, NOW)
    assert result["sample"] == 20
    assert {row["skill"]: row["percentage"] for row in result["skills"]} == {"python": 75, "typescript": 75, "sql": 25}
    assert next(row for row in result["skills"] if row["skill"] == "python")["declared"]
    serialized = json.dumps(result)
    for private in ["workmail", "user_id", "email", "person0"]:
        assert private not in serialized


@pytest.mark.parametrize("change", [{"user_id": 1}, {"email_verified": False}, {"email": "fake@example.com"}, {"email": "fake@x.test"}, {"email": "fake@x.invalid"}, {"location": "Cali"},
                                    {"participation": {"enabled": False}}, {"participation": {"enabled": True, "confirmed_real": True, "updated_at": "2025-01-01", "family": "software", "level": "junior"}}])
def test_ineligible_profile_cannot_push_a_group_over_threshold(change):
    assert peer_report(own(), [*[peer(i) for i in range(19)], peer(20, **change)], FILTERS, NOW)["status"] == "insufficient_data"


def test_fixed_cohorts_suppress_rare_and_universal_skills_and_round_percentages():
    peers = [peer(i, skills=["universal", *(["typescript"] if i < 16 else []), *(["rare"] if i < 4 else [])]) for i in range(23)]
    result = peer_report(own(), peers, FILTERS, NOW)
    assert result["skills"] == [{"skill": "typescript", "percentage": 70, "declared": False}]
    assert peer_report(own(), peers, {**FILTERS, "search": "unique person", "sector": "other", "modality": "remote"}, NOW) == result
    assert peer_report(own(), [*peers, peers[0]], FILTERS, NOW) == result
    assert peer_report(own(), peers, {**FILTERS, "location": ""}, NOW)["status"] == "choose_cohort"


def test_job_selection_deduplicates_and_excludes_demos_expired_and_wrong_cohorts():
    rows = [job(1), job(2, company_id=1, company_name="Empresa 1"), job(3, title="Backend Python · escenario"), job(4, company_name="Empresa ficticia"), job(5, external_url="https://example.com/job"),
            job(6, location="Cali"), job(7, quality_details={"seniority": "senior"}), job(8, title="Contador"), job(9, status="draft"), job(10, created_at=NOW - timedelta(days=91)), job(11, expires_at=NOW - timedelta(days=1)), job(12, source_name="local-quality-demo")]
    assert [row.id for row in selected_jobs(rows, FILTERS, NOW)] == [2]
    result = market_report(own(), rows, [], [], FILTERS, NOW)
    assert result["demand"]["sample"] == 1 and result["demand"]["skills"][0]["percentage"] is None


def test_salary_requires_twenty_distinct_companies_and_preserves_conditions():
    rows = [job(i) for i in range(20)]
    result = salary_report(rows, FILTERS)
    group = result["groups"][0]
    assert group["sample"] == 20 and group["offers"] == 20
    assert (group["p25"], group["median"], group["p75"]) == (2_475_000, 2_950_000, 3_425_000)
    assert salary_report([job(i, company_id=1) for i in range(30)], FILTERS)["status"] == "insufficient_data"
    assert salary_report(rows[:19] + [job(30, modality="remote")], FILTERS)["status"] == "insufficient_data"
    assert salary_report(rows[:19] + [job(30, quality_details={**job(30).quality_details, "weekly_hours": 48})], FILTERS)["status"] == "insufficient_data"
    assert salary_report(rows[:19] + [job(30, quality_details={**job(30).quality_details, "contract_type": "services"})], FILTERS)["status"] == "insufficient_data"
    # One company has one statistical vote, even with multiple offers.
    result = salary_report([*rows, job(40, company_id=19, salary=9_000_000)], FILTERS)
    assert result["groups"][0]["sample"] == 20 and result["groups"][0]["offers"] == 21


@pytest.mark.parametrize("missing", ["salary_currency", "salary_period", "salary_basis", "weekly_hours", "contract_type"])
def test_salary_never_guesses_missing_units_or_conditions(missing):
    details = job(30).quality_details; details.pop(missing)
    assert salary_report([*[job(i) for i in range(19)], job(30, quality_details=details)], FILTERS)["status"] == "insufficient_data"


def test_market_api_permissions_participation_withdrawal_and_explicit_skill(client):
    user, headers = register(client, "market-owner", skills=["python"], location="Medellín")
    _, company = company_account(client, "market-company")
    create_job(client, company)
    assert client.get("/api/v1/profiles/me/market").status_code == 401
    assert client.get("/api/v1/profiles/me/market", headers=company).status_code == 403
    assert client.get("/api/v1/profiles/me/market?family=unknown", headers=headers).status_code == 422
    response = client.get("/api/v1/profiles/me/market", params=FILTERS, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["peers"]["status"] == "insufficient_data"
    assert client.get("/api/v1/profiles/me/market", headers=headers).json()["demand"]["sample"] == 1
    path = "/api/v1/profiles/me/market/participation"
    choice = {"enabled": True, "family": "software", "level": "junior", "confirm_real_profile": True}
    assert client.put(path, headers=headers, json={**choice, "confirm_real_profile": False}).status_code == 422
    assert client.put(path, headers=headers, json=choice).status_code == 422  # Reserved test account.
    with client.session_factory() as db:
        owner = db.get(User, user["id"])
        owner.email = "market-owner@workmail.co"; owner.profile.location = "Medellín"; db.commit()
    assert client.put(path, headers=headers, json=choice).status_code == 200
    with client.session_factory() as db:
        assert db.get(User, user["id"]).profile.preferences["market_participation"]["enabled"]
    assert client.put(path, headers=headers, json={"enabled": False}).status_code == 200
    assert not client.get("/api/v1/profiles/me/market", params=FILTERS, headers=headers).json()["participation"]["enabled"]
    path = "/api/v1/profiles/me/market/skills"
    assert client.post(path, headers=headers, json={"skill": "TypeScript", "confirm": False}).status_code == 422
    assert client.post(path, headers=headers, json={"skill": "TypeScript", "confirm": True}).status_code == 200
    response = client.post(path, headers=headers, json={"skill": "typescript", "confirm": True})
    assert len(response.json()["skills"]) == 2


def test_repository_only_aggregates_verified_consented_candidates(client):
    user, headers = register(client, "market-viewer", location="Medellín")
    with client.session_factory() as db:
        for i in range(21):
            candidate = User(name=f"Private person {i}", email=f"market-peer-{i}@workmail.co", password_hash="unused", role="candidate", email_verified=i < 20)
            db.add(candidate); db.flush()
            db.add(Profile(user_id=candidate.id, location="Medellín", skills=["TypeScript"] if i < 15 else ["SQL"], preferences={"market_participation": {"enabled": True, "confirmed_real": True, "family": "software", "level": "junior", "updated_at": datetime.utcnow().isoformat() + "Z"}}))
        db.commit()
    response = client.get("/api/v1/profiles/me/market", params=FILTERS, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["peers"]["sample"] == 20
    assert "Private person" not in response.text and "workmail.co" not in response.text


def test_saving_design_changes_only_presentation_and_restores_options(client):
    _, headers = register(client, "design-owner", skills=["python"])
    _, company = company_account(client, "design-company")
    path = "/api/v1/profiles/me/resume-design"
    payload = {"style": "modern", "color": "teal", "sections": ["summary", "experiences"], "include_photo": False}
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    assert client.patch(path, headers=company, json=payload).status_code == 403
    assert client.patch(path, headers=headers, json={**payload, "style": "unknown"}).status_code == 422
    assert client.patch(path, headers=headers, json=payload).status_code == 200
    after = client.get("/api/v1/profiles/me", headers=headers).json()
    assert after["resume_export_options"] == {"sections": payload["sections"], "include_photo": False, "version": 2}
    assert after["resume_style"] == "modern" and after["resume_color"] == "teal"
    for field in ["skills", "profession", "experience", "experiences", "educations", "cv_text"]:
        assert after[field] == before[field]
