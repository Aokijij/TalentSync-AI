from datetime import datetime

from app.domain.services.external_job_content import (
    admission_reasons,
    extract_content,
    extract_external_skills,
    source_text,
    three_months_ago,
)

NOW = datetime(2026, 10, 29, 15)


def test_source_html_retains_paragraphs_bullets_and_never_script_text():
    text = source_text("<h2>Requisitos</h2><ul><li>SQL</li><li>Excel</li></ul><p>Trabajo híbrido.</p><script>invented</script>")
    assert "\n• SQL\n" in text and "\n• Excel\n" in text
    assert "invented" not in text and "<li>" not in text


def test_description_provides_sections_and_only_explicit_facts():
    raw = """<h2>About us</h2><p>We build products. Our founder has 20 years of experience.</p>
    <h2>What You'll Do</h2><ul><li>Build reports with SQL, Excel and Power BI.</li></ul>
    <h2>What We Look For</h2><ul><li>3–5 years of professional experience.</li></ul>
    <h2>Benefits</h2><p>Private health insurance.</p>
    <h2>Working conditions</h2><p>Indefinite-term contract.</p><p>Horario lunes a viernes de 8 a 17 horas.</p>"""
    content, details, requirements, relevant = extract_content("Senior Data Analyst", raw)
    assert {s["key"] for s in content["sections"]} >= {"requirements", "responsibilities", "benefits", "conditions"}
    assert details["seniority"] == "senior" and details["experience_months"] == 36
    assert details["contract_type"] == "indefinite" and "8 a 17" in details["schedule"]
    assert "3–5" in requirements and "founder" not in relevant
    assert "Build reports" in content["summary"]
    assert "salary_currency" not in details and "interview_count" not in details


def test_missing_data_remains_missing_and_semi_senior_is_not_senior():
    _, details, _, _ = extract_content("Analista", "Una oportunidad para trabajar con Excel, SQL y Python.")
    assert not details
    _, details, _, _ = extract_content("Desarrollador Semi Senior", "Desarrolla interfaces con React y TypeScript.")
    assert details["seniority"] == "mid"


def test_long_flat_colombian_advert_keeps_separate_requirements_and_functions():
    body = ("Auxiliar de Bodega Palabras clave: AuxiliarLogisticaInventarios ¡Hola! Trabaja en Cota. "
            "Responsabilidades: Realizar cargue y descargue de mercancía.Ejecutar picking y packing de pedidos. "
            "Requisitos: Experiencia mínima de un año en inventarios y uso de Excel. "
            "Beneficios: Formación y seguro de salud. "
            "Condiciones: Horario lunes a viernes de 8 a 17 horas. Contrato a término indefinido.")
    content, details, requirements, relevant = extract_content("Auxiliar de Bodega", body)
    keys = {s["key"] for s in content["sections"]}
    assert {"responsibilities", "requirements", "benefits", "conditions"} <= keys
    assert "Palabras clave" not in content["summary"]
    assert "Realizar" in content["summary"] and "un año" in requirements
    assert details["experience_months"] == 12
    assert details["schedule"].startswith("Horario") and "8 a 17" in details["schedule"]
    assert details["contract_type"] == "indefinite"


def test_age_is_based_on_source_publication_and_calendar_months():
    assert three_months_ago(datetime(2026, 5, 31)) == datetime(2026, 2, 28)
    skills = ["python", "sql", "excel"]
    assert not admission_reasons(datetime(2026, 7, 29, 15), skills, now=NOW)
    assert admission_reasons(datetime(2026, 7, 29, 14, 59), skills, now=NOW) == ["publication_too_old"]
    assert admission_reasons(None, skills, now=NOW) == ["publication_missing"]
    assert admission_reasons(datetime(2026, 10, 30), skills, now=NOW) == ["publication_in_future"]


def test_three_distinct_skills_cannot_be_met_with_aliases_or_filler():
    assert admission_reasons(NOW, ["Node.js", "nodejs", "SQL"], now=NOW) == ["insufficient_skills"]
    assert admission_reasons(NOW, ["Excel", "Excel avanzado", "SQL"], now=NOW) == ["insufficient_skills"]
    assert admission_reasons(NOW, ["HTML", "HTML5", "CSS3"], now=NOW) == ["insufficient_skills"]
    assert extract_external_skills("We need communication and accounting skills.") == ["comunicación", "contabilidad"]
    assert extract_external_skills("An opportunity to grow your career.") == []


def test_sector_skills_require_explicit_evidence_and_do_not_count_perks():
    skills = extract_external_skills("Preparación de alimentos, técnicas de cocina y trabajo en equipo. BPM.")
    assert set(skills) == {"preparación de alimentos", "técnicas de cocina", "trabajo en equipo"}
    assert "buenas prácticas de manufactura" not in skills  # BPM is ambiguous across sectors.
    pharmacy = extract_external_skills("Dispensación, farmacovigilancia y legislación farmacéutica.")
    assert set(pharmacy) == {"dispensación de medicamentos", "farmacovigilancia", "legislación farmacéutica"}
    assert extract_external_skills("Subsidio de transporte y bienestar.", ["transporte", "bienestar"]) == []
    assert extract_external_skills("Comunicación efectiva", ["comunicación efectiva", "comunicación"]) == ["comunicación"]


def test_technical_leadership_is_not_a_degree_and_missing_education_remains_unknown():
    content, _, _, _ = extract_content("Tech Lead", "Requirements\n6+ years of software engineering experience as the senior technical voice. This is a technical leadership role.")
    assert content["education"]["level"] is None
    assert "education_unspecified" in content["admission"]["information_gaps"]
    assert "education_unspecified" not in content["admission"]["clarity_reasons"]


def test_external_academic_alternatives_student_status_and_negotiable_salary_are_explicit():
    content, details, _, _ = extract_content("Analista Junior", "Funciones: Analizar datos y preparar reportes de resultados para los equipos de operaciones.\nRequisitos: Profesional en Contaduría Pública o estudiante de últimos semestres.\nExperiencia mínima de 1 año en contabilidad y manejo de Excel, SQL y Python.\nSalario: Por convenir")
    assert content["education"]["level"] == "university"
    assert details["education_accepts_in_progress"]
    assert content["compensation"]["status"] == "negotiable"
    assert content["admission"]["clarity_passed"]
