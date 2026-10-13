# ruff: noqa: F811
from io import BytesIO
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from pypdf import PdfReader
from test_api_flows import client, company_account, create_job, register  # noqa: F401

from app.api.schemas.profile import ProfileResponse, ProfileUpdate
from app.domain.entities.enums import UserRole
from app.domain.services.professions import education_match
from app.infrastructure.database.models import Company, CompanyMember, User


def test_only_one_current_job_can_be_saved_while_legacy_profiles_remain_readable():
    items = [{"is_current": True, "start_date": "2020-01"}, {"end_year": "Presente", "start_date": "2021-01"}]
    with pytest.raises(ValidationError, match="Solo puedes marcar un trabajo"):
        ProfileUpdate(experiences=items)
    assert len(ProfileResponse(id=1, user_id=1, experiences=items).experiences) == 2
    assert ProfileUpdate(experiences=[items[0], {"start_date": "2018-01", "end_date": "2019-12"}]).experiences[0]["is_current"]


def test_current_studies_have_explicit_status_and_cannot_claim_a_completion_year():
    item = {"degree": "Ingeniería de sistemas", "institution": "Universidad", "start_year": "2024", "is_current": True}
    assert ProfileUpdate(educations=[item]).educations[0]["is_current"]
    with pytest.raises(ValidationError, match="año de finalización"):
        ProfileUpdate(educations=[{**item, "end_year": "2025"}])
    with pytest.raises(ValidationError, match="posterior al inicio"):
        ProfileUpdate(educations=[{"start_year": "2025", "end_year": "2024"}])
    with pytest.raises(ValidationError, match="años válidos"):
        ProfileUpdate(educations=[{"start_year": "3000"}])
    profile = SimpleNamespace(educations=[item], profession=item["degree"], education=item["degree"])
    job = SimpleNamespace(required_study_fields=[], required_education_level="university")
    assert education_match(profile, job) == 70  # In-progress field relevance is retained, completed level is not claimed.


def test_profile_api_preserves_study_status_and_rejects_multiple_current_jobs(client):
    _, candidate = register(client, "profile-current")
    payload = {"educations": [{"degree": "Ingeniería de sistemas", "start_year": "2024", "is_current": True}],
               "experiences": [{"role": "Analista", "start_date": "2020-02", "is_current": True}]}
    response = client.put("/api/v1/profiles/me", headers=candidate, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["educations"][0]["is_current"] is True
    pdf = client.get("/api/v1/profiles/me/export", headers=candidate)
    assert pdf.status_code == 200 and "En curso" in " ".join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
    payload["experiences"].append({"role": "Asistente", "start_date": "2018-01", "is_current": True})
    assert client.put("/api/v1/profiles/me", headers=candidate, json=payload).status_code == 422
    assert len(client.get("/api/v1/profiles/me", headers=candidate).json()["experiences"]) == 1


def member_account(client, name, company_id, role, active=True):
    account, _ = register(client, name)
    with client.session_factory() as db:
        db.get(User, account["id"]).role = UserRole.COMPANY
        member = CompanyMember(company_id=company_id, user_id=account["id"], role=role, active=active, assigned_job_ids=[])
        db.add(member)
        db.commit()
        member_id = member.id
    from app.infrastructure.security.jwt import create_access_token
    return member_id, {"Authorization": f"Bearer {create_access_token(str(account['id']), 'company')}"}


def test_recruiters_assign_only_active_interviewers_and_jobs_in_their_own_company(client):
    owner, headers = company_account(client, "dispatch-owner")
    own_job = create_job(client, headers)
    with client.session_factory() as db:
        company_id = db.query(Company).filter_by(owner_user_id=owner["id"]).one().id
    recruiter_id, recruiter = member_account(client, "dispatch-recruiter", company_id, "recruiter")
    interviewer_id, interviewer = member_account(client, "dispatch-interviewer", company_id, "interviewer")
    inactive_id, _ = member_account(client, "dispatch-inactive", company_id, "interviewer", active=False)
    _, other_owner = company_account(client, "dispatch-other")
    other_job = create_job(client, other_owner)
    endpoint = f"/api/v1/organization/interview-team/{interviewer_id}"
    assert [row["id"] for row in client.get("/api/v1/organization/interview-team", headers=recruiter).json()] == [interviewer_id]
    assert client.patch(endpoint, headers=recruiter, json={"assigned_job_ids": [own_job["id"]]}).status_code == 200
    assert [row["job_id"] for row in client.get("/api/v1/organization/assignments", headers=interviewer).json()] == [own_job["id"]]
    assert client.patch(endpoint, headers=recruiter, json={"assigned_job_ids": [other_job["id"]]}).status_code == 422
    assert client.patch(endpoint, headers=other_owner, json={"assigned_job_ids": []}).status_code == 404
    assert client.patch(endpoint, headers=interviewer, json={"assigned_job_ids": []}).status_code == 403
    assert client.patch(endpoint, headers=recruiter, json={"assigned_job_ids": [], "role": "recruiter"}).status_code == 422
    assert client.patch(f"/api/v1/organization/interview-team/{inactive_id}", headers=recruiter, json={"assigned_job_ids": []}).status_code == 404
    assert client.patch(f"/api/v1/organization/interview-team/{recruiter_id}", headers=recruiter, json={"assigned_job_ids": []}).status_code == 404
    assert client.patch(f"/api/v1/organization/team/{interviewer_id}", headers=recruiter, json={"role": "recruiter", "active": True}).status_code == 403
    assert client.patch(endpoint, headers=recruiter, json={"assigned_job_ids": []}).status_code == 200
    assert client.get("/api/v1/organization/assignments", headers=interviewer).json() == []
