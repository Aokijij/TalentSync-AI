from app.infrastructure.nlp.text_processor import text_processor

TABLE_CV = """PERSONA DE PRUEBA
ESTUDIANTE DE INGENIERÍA DE SISTEMAS | QA Y ANÁLISIS DE DATOS
Medellín, Colombia | 300 000 0000 | persona@example.test
PERFIL PROFESIONAL     Estudiante de Ingeniería de Sistemas con formación en Scrum.
Interesada en pruebas de software y análisis de datos. Participación en proyectos académicos.
COMPETENCIAS TÉCNICAS  QA Y PRUEBAS: pruebas funcionales, historias de usuario, trazabilidad.
ANÁLISIS DE DATOS: Excel y SQL.
PROYECTOS             PLAYRECORD | Proyecto académico
• Participación en el análisis de requerimientos e historias de usuario.
• Apoyo en pruebas funcionales y seguimiento de errores.
TASKFLOW | Proyecto académico
• Organización de historias de usuario bajo Scrum.
CUENTA CLARA | Proyecto personal en desarrollo
• Registro de ventas diarias y cuentas por cobrar para un negocio familiar.
LINGUA | Proyecto personal
• Aplicación web para aprendizaje de idiomas.
• Enlace: lingua-example.vercel.app
FORMACIÓN ACADÉMICA    INGENIERÍA DE SISTEMAS
Universidad de Prueba | En curso
CERTIFICACIÓN E IDIOMAS Scrum Fundamentals Certified (SFC) — SCRUMstudy | Mayo de 2026
Español: nativo | Inglés: A2 (básico)
"""


def test_table_cv_extracts_project_facts_summary_certification_and_explicit_languages():
    result = text_processor.analyze_cv(TABLE_CV)
    assert result.professional_summary.startswith("Estudiante de Ingeniería")
    assert "COMPETENCIAS" not in result.professional_summary
    assert {row["title"] for row in result.projects} == {"PLAYRECORD", "TASKFLOW", "CUENTA CLARA", "LINGUA"}
    assert result.projects[-1]["url"] == "https://lingua-example.vercel.app"
    certificate = next(row for row in result.certifications if "Scrum Fundamentals" in row["name"])
    assert certificate["issuer"] == "SCRUMstudy" and certificate["year"] == "2026"
    assert result.languages == [{"name": "español", "level": "NATIVE"}, {"name": "inglés", "level": "A2"}]


def test_english_cv_with_inline_headers_does_not_mix_project_or_skill_text_into_summary():
    text = """PROFESSIONAL SUMMARY: Data analyst with experience in reporting.
TECHNICAL SKILLS: Python, SQL, Excel
SELECTED PROJECTS
REVENUE DASHBOARD | Project
- Built SQL reporting pipelines and documented data quality checks.
EDUCATION
University of Test
CERTIFICATIONS
Data Analytics Certificate — Example Academy | 2025
LANGUAGES
English B2 | Spanish Native
"""
    result = text_processor.analyze_cv(text)
    assert result.professional_summary == "Data analyst with experience in reporting."
    assert len(result.projects) == 1 and "SQL reporting" in result.projects[0]["description"]
    assert result.languages == [{"name": "inglés", "level": "B2"}, {"name": "español", "level": "NATIVE"}]


def test_unspecified_language_level_is_not_invented():
    result = text_processor.analyze_cv("IDIOMAS\nInglés: intermedio\nFrancés: C1\nPROYECTOS\n")
    assert result.languages == [{"name": "francés", "level": "C1"}]
    assert not result.projects


def test_alternative_pdf_reading_order_does_not_append_summary_twice():
    from app.infrastructure.nlp.cv_sections import extract_sections
    text = "PERFIL PROFESIONAL\nAnalista de datos.\nTexto lateral que interrumpe la lectura.\nPYPDF FALLBACK\nPERFIL PROFESIONAL\nAnalista de datos.\nEXPERIENCIA\nEmpresa de prueba"
    assert extract_sections(text)["summary"] == "Analista de datos."
