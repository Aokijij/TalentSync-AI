from types import SimpleNamespace as Row

import pytest

from app.domain.services.academic_fields import academic_name, catalog, compare_fields
from app.domain.services.academic_matching import education_evaluation
from app.domain.services.professions import education_match


def job(fields=None, level="university", **details):
    return Row(
        required_study_fields=fields or ["Contaduría Pública"],
        required_education_level=level,
        quality_details=details,
    )


def profile(degree, level="university", **extra):
    return Row(educations=[{"degree": degree, "level": level, **extra}])


@pytest.mark.parametrize(
    "name", ["CONTADURÍA PÚBLICA", " Contaduria Publica ", "Contabilidad"]
)
def test_normalized_names_and_registered_variants(name):
    result = education_evaluation(profile(name), job(education_field_policy="exact"))
    assert result["score"] == 100 and result["status"] == "fulfilled"


@pytest.mark.parametrize(
    "name", ["Economía", "Finanzas", "Administración de Empresas", "Medicina"]
)
def test_broad_financial_or_other_families_do_not_satisfy_accounting(name):
    assert education_evaluation(profile(name), job())["status"] == "not_met"
    assert education_match(profile(name), job()) == 0


def test_related_programs_are_partial_and_company_can_exclude_them():
    candidate = profile("Ingeniería Informática")
    target = job(["Ingeniería de Sistemas"], education_field_policy="related")
    result = education_evaluation(candidate, target)
    assert result["score"] == 79 and result["status"] == "partial"
    assert result["selected"]["field_score"] == 70
    assert result["selected"]["level_score"] == 100
    target.quality_details["education_field_policy"] = "exact"
    assert education_match(candidate, target) == 0
    target.required_study_fields.append("Ingeniería Informática")
    assert education_match(candidate, target) == 100


def test_unknown_names_require_review_and_exact_declared_names_still_match():
    candidate = profile("Estudios de nuevos sistemas financieros")
    result = education_evaluation(candidate, job())
    assert result["score"] is None and result["status"] == "review"
    assert compare_fields("contaduria inventada", "Contaduría")["status"] == "review"
    assert (
        education_evaluation(candidate, job([candidate.educations[0]["degree"]]))[
            "status"
        ]
        == "fulfilled"
    )


def test_related_title_cannot_borrow_level_from_unrelated_degree():
    candidate = Row(
        educations=[
            {"degree": "Derecho", "level": "postgraduate"},
            {"degree": "Contabilidad", "level": "technical"},
        ]
    )
    result = education_evaluation(candidate, job())
    assert result["score"] == 80 and result["status"] == "partial"
    assert result["selected"]["actual_level"] == "technical"


def test_ongoing_studies_and_level_only_requirements_are_independent():
    candidate = profile("Contaduría Pública", is_current=True)
    assert education_match(candidate, job()) == 70
    assert education_match(candidate, job(education_accepts_in_progress=True)) == 100
    target = Row(
        required_study_fields=[],
        required_education_level="university",
        quality_details={},
    )
    assert education_match(candidate, target) == 0
    target.quality_details["education_accepts_in_progress"] = True
    assert education_match(candidate, target) == 100


def test_missing_education_is_review_and_profession_alone_does_not_prove_studies():
    assert (
        education_evaluation(
            Row(educations=[], education="", profession="Contaduría Pública"), job()
        )["status"]
        == "review"
    )
    result = education_evaluation(Row(educations=[]), job())
    assert result["score"] is None
    assert (
        education_evaluation(
            profile("Contaduría"),
            Row(required_study_fields=[], required_education_level=None),
        )["status"]
        == "not_required"
    )


def test_catalog_is_versioned_traceable_and_aliases_are_unambiguous():
    data = catalog()
    assert (
        data["version"]
        and data["reviewed_at"]
        and data["classification"]["source_url"].startswith("https://www.dane.gov.co/")
    )
    seen = {}
    for row in data["programs"]:
        for alias in [row["label"], *row["aliases"]]:
            key = academic_name(alias)
            assert key not in seen or seen[key] == row["id"], (
                alias,
                seen.get(key),
                row["id"],
            )
            seen[key] = row["id"]
