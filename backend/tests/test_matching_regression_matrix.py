"""Synthetic regression matrix; does not estimate real hiring success or fairness."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.application.use_cases.matching import candidate_match
from app.domain.services.match_explanations import explain
from app.infrastructure.nlp.text_processor import TextProcessor


def test_synthetic_matching_orders_skills_and_excludes_identity():
    nlp = TextProcessor()
    job = SimpleNamespace(title="Desarrollador Python", description="Desarrollo de APIs Python y SQL",
                          requirements="Python SQL", skills=["python", "sql"], embedding=[], languages=[],
                          skill_requirements=[], required_study_fields=[], required_education_level=None,
                          sector="Tecnologia", salary=5000000, modality="remote", location=None)
    cases = []
    for skills in [[], ["python"], ["Python", "SQL"], ["python", "Python", "sql", "SQL"]]:
        scores = []
        for identity in range(4):
            profile = SimpleNamespace(profession="Desarrollador Python", experience="Desarrollo de APIs",
                                      skills=skills, embedding=[], education=None, experiences=[],
                                      educations=[{"institution": f"Institución sintética {identity}", "degree": ""}],
                                      certifications=[], languages=[], preferences={}, evidence=[],
                                      phone=f"555000{identity}", user=SimpleNamespace(name=f"Persona {identity}",
                                      email=f"identity-{identity}@example.com"))
            result = candidate_match(profile, job, nlp=nlp)
            score, context, coverage, language, confidence, education, certificates = result
            detail = explain(profile, job, context=context, skills=coverage, language=language,
                             confidence=confidence, education=education, certifications=certificates,
                             percentage=score)
            assert 0 <= score <= 100
            assert sum(row["points"] for row in detail["components"]) == pytest.approx(score, abs=.02)
            assert detail["score_type"] == "compatibility_index"
            scores.append(score)
        assert len(set(scores)) == 1
        cases.append(scores[0])
    assert cases[0] < cases[1] < cases[2]
    # Repeated declarations cannot raise skill coverage. Text repetitions may
    # change lexical context, so compare coverage rather than total score.
    profile.skills = ["python", "sql"]
    baseline = candidate_match(profile, job, nlp=nlp)
    profile.skills *= 3
    assert candidate_match(profile, job, nlp=nlp)[2] == baseline[2] == 100
    job.skills, job.skill_requirements = ["spring boot"], [{"skill": "spring boot", "essential": True, "weight": 1}]
    profile.skills = ["java", "arquitectura MVC"]
    related = candidate_match(profile, job, nlp=nlp)
    assert related[2] == 0  # Foundation is not verified Spring Boot proficiency.
    profile.skills = ["springboot"]
    assert candidate_match(profile, job, nlp=nlp)[2] == 100
    internal = candidate_match(profile, job, nlp=nlp)
    job.source_kind = "external"
    external = candidate_match(profile, job, nlp=nlp)
    assert external[0] <= internal[0] and external[4] < 100
    if os.getenv("TALENTSYNC_LOCAL_REHEARSAL") == "1":
        destination = Path(__file__).resolve().parents[2] / ".local/verification"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "matching-regressions.json").write_text(json.dumps({"passed": True,
            "scope": "synthetic lexical regression; not hiring accuracy or demographic fairness",
            "identity_variants": 16, "checks": ["coverage ordering", "identity invariance", "score bounds",
            "component totals", "duplicate skills", "related skills are not equivalents", "aliases",
            "external confidence penalty"]}, indent=2), encoding="utf-8")
