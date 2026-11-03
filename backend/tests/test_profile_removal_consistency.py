# ruff: noqa: F811
from test_api_flows import client, company_account, create_job, register  # noqa: F401


def test_removing_studies_and_skills_clears_legacy_matching_context(client):
    _, headers = register(client, "delete-profile-context", skills=["python", "sql"])
    original = client.get("/api/v1/profiles/me", headers=headers).json()
    original.update(education="Estudio anterior", educations=[{"degree": "Ingeniería de Sistemas", "institution": "Universidad de prueba", "start_year": "2018", "end_year": "2023", "level": "university"}], summary_mode="automatic")
    saved = client.put("/api/v1/profiles/me", headers=headers, json=original)
    assert saved.status_code == 200, saved.text
    _, employer = company_account(client, "profile-removal-employer")
    create_job(client, employer)
    before_scores = client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=headers).json()
    assert before_scores and before_scores[0]["match_percentage"] > 0
    updated = saved.json()
    updated.update(educations=[], experiences=[], certifications=[], skills=[], profession=None, experience=None, preferred_sector=None)
    removed = client.put("/api/v1/profiles/me", headers=headers, json=updated)
    assert removed.status_code == 200, removed.text
    assert not removed.json()["education"] and not removed.json()["experience"]
    assert not client.get("/api/v1/profiles/me", headers=headers).json()["educations"]
    scores = client.get("/api/v1/recommendations/me/jobs?include_all=true", headers=headers).json()
    assert scores and all(item["match_percentage"] == 0 for item in scores)


def test_replacing_cv_does_not_mix_old_work_or_studies_and_reimport_does_not_duplicate(client):
    from test_cv_template_roundtrip import CV

    from app.api.deps import get_resume_reader
    _, headers = register(client, "replace-imported-profile", skills=["WordPress"])
    original = client.get("/api/v1/profiles/me", headers=headers).json()
    original.update(experiences=[{"role": "Registro anterior", "company": "Empresa anterior", "start_year": "2010", "end_year": "2011", "description": "Información que se reemplazará"}], educations=[{"degree": "Estudio anterior", "institution": "Institución anterior", "end_year": "2010"}])
    client.put("/api/v1/profiles/me", headers=headers, json=original).raise_for_status()
    class Reader:
        def extract(self, *_):
            return "review.pdf", CV
    client.app.dependency_overrides[get_resume_reader] = lambda: Reader()
    for _ in range(2):
        response = client.post("/api/v1/profiles/me/cv?replace_profile=true", headers=headers, files={"file": ("review.pdf", b"%PDF-review", "application/pdf")})
        assert response.status_code == 200, response.text
        profile = response.json()
        assert len(profile["experiences"]) == 3 and len(profile["educations"]) == 2
        assert all(row["company"] != "Empresa anterior" for row in profile["experiences"])
        assert "wordpress" not in profile["skills"]
