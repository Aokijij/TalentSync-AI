"""Synthetic PDFs exercise the reader and parser without publishing real CVs."""
import pytest
from reportlab.pdfgen.canvas import Canvas

from app.infrastructure.nlp.pdf_reader import _extract_pypdf_text
from app.infrastructure.nlp.text_processor import text_processor


@pytest.mark.parametrize("sidebar_right", [False, True])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("wide_header", [False, True])
def test_columns_keep_jobs_studies_and_project_cards_separate(tmp_path, sidebar_right, nested, wide_header):
    path = tmp_path / "synthetic.pdf"
    canvas = Canvas(str(path), pagesize=(640, 900))
    side, body = (440, 30) if sidebar_right else (30, 240)

    def block(x, y, lines, bold=False):
        text = canvas.beginText(x, y)
        text.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        text.setLeading(14)
        for line in lines.split("\n"):
            text.textLine(line)
        canvas.drawText(text)

    # A full-width header and scrambled drawing order mimic design exports.
    block(30 if wide_header else body, 870,
          "PERSONA DE PRUEBA CON ENCABEZADO A TODO EL ANCHO" if wide_header else "PERSONA DE PRUEBA", True)
    block(body, 845, "ANALISTA DE SISTEMAS", True)
    if nested:
        canvas.beginForm("content")
    block(side, 790, "EDUCACIÓN", True)
    block(side, 765, "2020 - Presente\nUNIVERSIDAD DE PRUEBA\nIngeniería de Sistemas e\nInformática")
    block(side, 680, "2017 - 2019\nSENA\nTecnólogo en Desarrollo\nde Sistemas de Información")
    block(side, 590, "HABILIDADES", True)
    block(side, 565, "JavaScript\nPython\nQA Testing")
    block(body, 810, "PERFIL PROFESIONAL", True)
    block(body, 790, "Analista con experiencia en software y pruebas.")
    block(body, 750, "EXPERIENCIA LABORAL", True)
    for company, role, period, y, duties in [
        ("Empresa Alfa SAS", "DESARROLLADOR FRONT-END", "2018 - 2019", 720, "Interfaces con HTML y JavaScript.\nIntegración de APIs REST.\nMejora continua."),
        ("Empresa Beta", "ANALISTA QA", "2019 - 2020", 610, "Pruebas funcionales.\nSeguimiento de incidencias.\nDocumentación de calidad."),
        ("Empresa Gamma", "ANALISTA DE INVENTARIO", "2022 - 2023", 500, "Control de inventario.\nReportes e indicadores.\nCalidad de datos."),
    ]:
        block(body, y - 40, duties)
        block(body + 275, y, period)
        block(body, y, company, True)
        block(body, y - 20, role)
    block(body, 380, "PROYECTOS", True)
    block(body, 350, "Proyecto Alfa", True)
    block(body, 330, "Gestión de tareas.\nInterfaz en React.")
    block(body + 190, 350, "Proyecto Beta", True)
    block(body + 190, 330, "Análisis de perfiles.\nDesarrollo Full Stack.")
    if nested:
        canvas.endForm()
        canvas.doForm("content")
    canvas.save()
    result = text_processor.analyze_cv(_extract_pypdf_text(str(path)))
    assert result.profession == "Analista De Sistemas"
    assert [(row["company"], row["role"], row["start_year"], row["end_year"]) for row in result.experiences] == [
        ("Empresa Alfa SAS", "DESARROLLADOR FRONT-END", "2018", "2019"),
        ("Empresa Beta", "ANALISTA QA", "2019", "2020"),
        ("Empresa Gamma", "ANALISTA DE INVENTARIO", "2022", "2023"),
    ]
    assert "Mejora continua" in result.experiences[0]["description"]
    assert "Documentación de calidad" in result.experiences[1]["description"]
    assert "Calidad de datos" in result.experiences[2]["description"]
    assert all("Proyecto" not in row["description"] and "Universidad" not in row["description"] for row in result.experiences)
    assert all(not row.get("start_date") and not row.get("end_date") for row in result.experiences)
    assert len(result.educations) == 2
    assert result.educations[0]["degree"] == "Ingeniería de Sistemas e Informática"
    assert {row["title"] for row in result.projects} == {"Proyecto Alfa", "Proyecto Beta"}


def test_english_timeline_preserves_role_outside_spanish_job_dictionary():
    result = text_processor.analyze_cv("""WORK EXPERIENCE
Example Company (Jan 2021 - Feb 2023)
Product Owner
Led delivery and coordinated product releases.
PROJECTS
Project: Sample
Created a dashboard.
EDUCATION
Engineering in Computing
""")
    assert len(result.experiences) == 1
    assert result.experiences[0]["role"] == "Product Owner"
    assert result.experiences[0]["start_date"] == "2021-01"
    assert "dashboard" not in result.experiences[0]["description"]


def test_degree_words_in_job_duties_are_not_additional_studies():
    result = text_processor.analyze_cv("""EDUCACIÓN
2020 - 2024
UNIVERSIDAD EJEMPLO
Ingeniería Industrial
EXPERIENCIA LABORAL
Empresa Uno (2024 - 2025)
Cargo: Analista
Funciones:
Ingeniería de procesos para mejorar operaciones.
""")
    assert [row["degree"] for row in result.educations] == ["Ingeniería Industrial"]
