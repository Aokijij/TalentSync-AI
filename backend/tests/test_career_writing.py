from types import SimpleNamespace

import pytest

from app.domain.services.career_coach import document_review
from app.domain.services.career_writing import (
    rewrite_experience,
    validate_generated_text,
)


@pytest.mark.parametrize(("source", "expected"), [
    ("Atención a pacientes\nApoyo en la elaboración de registros", "Atendí a pacientes. Apoyé en la elaboración de registros."),
    ("Gestión de pedidos\nElaboración de reportes con Excel", "Gestioné pedidos. Elaboré reportes con Excel."),
    ("Desarrollo de interfaces con React\nValidación de información", "Desarrollé interfaces con React. Validé información."),
    ("Yo hacía reportes\nApoyaba al equipo", "Elaboré reportes. Apoyé al equipo."),
])
def test_local_generation_rewrites_different_occupations_without_extra_facts(source, expected):
    proposal = rewrite_experience({"description": source})
    assert proposal["text"] == expected
    assert proposal["method"] == "local"
    assert proposal["questions"]
    assert not any(word in proposal["text"].lower() for word in ("lideré", "%", "aws"))


def test_generation_preserves_numbers_qualifications_and_ongoing_employment():
    source = "Apoyo en el control de 25 pedidos\nNo tengo experiencia en AWS\nElaboración de 2 reportes con Excel"
    row = rewrite_experience({"description": source, "is_current": True}, style="bullets", result="El equipo consulta los reportes.")
    assert row["text"] == "• Apoyo en el control de 25 pedidos.\n• No tengo experiencia en AWS.\n• Elaboro 2 reportes con Excel.\n• El equipo consulta los reportes."
    assert row["questions"] == []
    with pytest.raises(ValueError):
        rewrite_experience({"description": ""})
    with pytest.raises(ValueError):
        rewrite_experience({"description": "Preparaba reportes"}, result="Mejoré [X]%")


def test_document_review_points_to_fields_and_does_not_count_dates_as_phone():
    profile = SimpleNamespace(experiences=[{"role": "Auxiliar", "company": "Clínica"}], educations=[{"degree": "Enfermería", "institution": "Instituto"}], skills=["excel", "sql"])
    text = "contacto@example.com\n2019 - 2022\nAuxiliar\nClínica\nEnfermería\nInstituto\nExcel"
    checks = document_review(profile, text)
    assert not checks[0]["ok"]
    assert all(check["ok"] for check in checks[1:])
    assert [check["target"] for check in checks] == ["profile-contact", "profile-experiences", "profile-educations", "profile-skills"]
    assert "sql" not in checks[3]["detail"]
    assert document_review(profile, text + "\n+57 300 123 4567")[0]["ok"]


@pytest.mark.parametrize("text", ["Aumenté las ventas un 25%.", "Implementé AWS.", "Lideré un equipo.", "Atendí pacientes."])
def test_ai_rejects_unsupported_metrics_tools_leadership_and_loss_of_support(text):
    with pytest.raises(ValueError):
        validate_generated_text({"text": text}, {"description": "Apoyo en atención a pacientes"})


def test_ai_preserves_explicit_negation_and_uses_candidate_result():
    with pytest.raises(ValueError):
        validate_generated_text({"text": "Tengo experiencia en AWS."}, {"description": "No tengo experiencia en AWS"})
    response = validate_generated_text({"text": "Preparé 2 reportes con Excel para la consulta del equipo.", "idea": "¿Qué datos incluían?"}, {"description": "Preparaba reportes con Excel"}, "Entregué 2 reportes")
    assert response["method"] == "local-ai" and response["questions"] == ["¿Qué datos incluían?"]


def test_ai_filters_standalone_promotional_claims_and_keeps_current_tense():
    response = validate_generated_text({"text": "Mi trabajo se centró en atender clientes y seguir pedidos. Además, mejoré la eficiencia de la empresa.", "idea": "¿Qué pedidos atendías?"}, {"description": "Atención a clientes. Seguimiento de pedidos.", "is_current": True})
    assert response["text"] == "Mi trabajo se centra en atender clientes y seguir pedidos."
