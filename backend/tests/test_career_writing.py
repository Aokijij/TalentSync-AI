from types import SimpleNamespace

import pytest

from app.domain.services.career_coach import document_review
from app.domain.services.career_writing import rewrite_experience


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
