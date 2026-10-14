from copy import deepcopy
from types import SimpleNamespace

from app.application.use_cases.matching import candidate_match
from app.domain.services.match_explanations import explain
from app.domain.services.professions import required_certification_match
from app.domain.services.writing_context import (
    original_context_profile,
    remember_writing_context,
)


class ContextNlp:
    def matching_similarity(self, left, right, vector):
        return 90 if "reportes" in left.lower() else 20
    def embed(self, text):
        return []


def data():
    p = SimpleNamespace(profession="Analista", skills=["python"], experiences=[{"role": "Analista", "description": "Elaboración de reportes con Python", "start_date": "2020-01", "end_date": "2022-12"}], experience="", education="", educations=[], certifications=[], evidence=[], preferences={}, languages=[], preferred_sector="")
    p.embedding = []
    j = SimpleNamespace(title="Analista Python", description="Elaborar reportes", requirements="Python", skills=["python"], skill_requirements=[], required_education_level="university", required_study_fields=[], languages=[], sector="", source_kind="internal", quality_details={})
    j.embedding, j.salary, j.modality, j.location = [], None, "remote", ""
    return p, j


def test_unrequested_courses_do_not_reduce_compatibility_or_create_a_zero_certification_component():
    p, j = data()
    first = candidate_match(p, j, nlp=ContextNlp())
    p.certifications = [{"name": "Atención al cliente", "issuer": "Centro"}]
    after = candidate_match(p, j, nlp=ContextNlp())
    assert after == first
    details = explain(p, j, context=after[1], skills=after[2], language=after[3], confidence=100, education=after[5], certifications=after[6], percentage=after[0])
    assert "certifications" not in [row["key"] for row in details["components"]]
    assert abs(sum(row["points"] for row in details["components"]) - after[0]) < .02


def test_explicit_required_certificate_is_evaluated_even_when_candidate_has_none():
    p, j = data()
    j.requirements = "Certificación AWS obligatoria"
    assert required_certification_match(p, j) == 0
    p.certifications = [{"name": "AWS", "issuer": "Amazon"}]
    assert required_certification_match(p, j) == 100
    j.requirements = "Certificación AWS deseable"
    assert required_certification_match(p, j) is None


def test_accepted_rewrite_retains_original_context_and_manual_edits_invalidate_it():
    p, j = data()
    before = candidate_match(p, j, nlp=ContextNlp())
    original = deepcopy(p.experiences[0])
    proposal = {"index": 0, "record": original, "after": "Preparé informes utilizando Python"}
    p.experiences[0] = {**original, "description": proposal["after"]}
    remember_writing_context(p, proposal, True)
    unchanged = deepcopy(p.experiences)
    assert candidate_match(p, j, nlp=ContextNlp())[0] >= before[0]
    assert p.experiences == unchanged
    p.experiences[0]["description"] = "Otra experiencia confirmada posteriormente"
    assert original_context_profile(p) is None
    remember_writing_context(p, proposal, False)
    assert p.preferences["writing_contexts"] == []


def test_source_context_is_used_only_for_the_exact_accepted_record():
    p, j = data()
    record = deepcopy(p.experiences[0])
    p.preferences["writing_contexts"] = [{"index": 0, "record": record, "after": "Preparé informes utilizando Python"}]
    assert original_context_profile(p) is None
    p.experiences[0]["description"] = "Preparé informes utilizando Python"
    assert original_context_profile(p).experiences[0] == record
    p.experiences[0]["company"] = "Otra organización"
    assert original_context_profile(p) is None
