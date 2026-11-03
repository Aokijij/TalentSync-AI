from textwrap import dedent

import pytest

from app.application.use_cases.profiles import _merge_imported
from app.domain.services.cv_periods import period_fields
from app.domain.services.experience_dates import experience_months
from app.infrastructure.nlp.text_processor import text_processor


@pytest.mark.parametrize(
    "text,start,end",
    [
        ("Julio 2025 – Noviembre 2025", "2025-07", "2025-11"),
        ("Jul. de 2025 hasta Nov. de 2025", "2025-07", "2025-11"),
        ("07/2025 - 11/2025", "2025-07", "2025-11"),
        ("2025-07 — 2025-11", "2025-07", "2025-11"),
        ("July 2025 to November 2025", "2025-07", "2025-11"),
    ],
)
def test_explicit_months_are_preserved(text, start, end):
    row = period_fields(text)
    assert row["start_date"] == start and row["end_date"] == end
    assert row["start_year"] == row["end_year"] == "2025"


def test_year_only_and_current_jobs_do_not_invent_dates():
    assert period_fields("2021 – 2023") == {"start_year": "2021", "end_year": "2023"}
    assert period_fields("Marzo 2024 - Actualidad") == {
        "start_year": "2024",
        "end_year": "Presente",
        "start_date": "2024-03",
        "is_current": True,
    }


def test_company_heading_extracts_months_and_five_month_duration():
    cv = dedent("""\
        EXPERIENCIA LABORAL
        Avinal (Julio 2025 – Noviembre 2025)
        Cargo: Analista de Proyectos.
        Jefe inmediato: Persona de contacto
        Funciones:
        • Planeación y estructuración de proyectos
        • Seguimiento y control de la ejecución
        • Gestión documental del proyecto
        • Seguimiento a indicadores de desempeño
    """)
    rows, _, _ = text_processor.extract_resume_items(cv)
    assert len(rows) == 1
    assert rows[0]["start_date"] == "2025-07" and rows[0]["end_date"] == "2025-11"
    assert experience_months(rows) == 5
    assert "Planeación" in rows[0]["description"]


def test_same_year_rehires_stay_separate_and_year_only_import_is_enriched():
    base = {
        "company": "Empresa",
        "role": "Analista",
        "start_year": "2025",
        "end_year": "2025",
    }
    first = {**base, "start_date": "2025-01", "end_date": "2025-03"}
    second = {**base, "start_date": "2025-07", "end_date": "2025-11"}
    assert len(_merge_imported([first], [second], ("role", "company"))) == 2
    assert (
        _merge_imported([base], [second], ("role", "company"))[0]["start_date"]
        == "2025-07"
    )
    assert len(text_processor._merge_resume_experiences([first, second])) == 2


@pytest.mark.parametrize("period", ["Julio 2025 – Noviembre 2025", "07/2025 - 11/2025", "2025-07 - 2025-11"])
def test_role_first_periods_keep_month_precision(period):
    rows, _, _ = text_processor.extract_resume_items(f"EXPERIENCIA LABORAL\nAnalista de proyectos\nEmpresa Ejemplo\nFunciones: Planeación y seguimiento.\n{period}\n")
    assert rows
    assert rows[0]["start_date"] == "2025-07" and rows[0]["end_date"] == "2025-11"
