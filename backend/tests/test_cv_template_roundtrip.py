from app.infrastructure.nlp.text_processor import text_processor

CV = """Persona de prueba
Analista de sistemas
contacto@example.com · +57 300-123-4567 · Medellín, Antioquia

Perfil profesional
Analista de sistemas con experiencia en pruebas funcionales y desarrollo de interfaces.
Conocimientos en Python, SQL y JavaScript.

Experiencia laboral
ANALISTA QA · Empresa Uno SAS
jul. 2019 - feb. 2020
Diseño y ejecución de pruebas funcionales con documentación de incidencias.
ANALISTA DE INVENTARIO · Empresa Dos
dic. 2022 - oct. 2023
Control de inventarios y elaboración de reportes.
DESARROLLADOR FRONT-END · Empresa Tres S.A.
jun. 2018 - feb. 2019
Desarrollo de interfaces con HTML, CSS y JavaScript.

Formación académica
Ingeniería de Sistemas e Informática · Universidad de Prueba
2020 - En curso
Tecnólogo en Desarrollo de Sistemas · Instituto de Prueba
2017 - 2019
Hoja de vida                                      Página 1

Muestras de trabajo
Proyecto universitario
Habilidades
Python · SQL · JavaScript
Idiomas
inglés: B1
Preferencias laborales
Tecnologia y software · Remoto · Inmediata
"""


def test_exported_cv_recovers_contacts_summary_jobs_and_each_study_period():
    result = text_processor.analyze_cv(CV)
    assert result.location == "Medellín, Antioquia"
    assert result.experience.startswith("Analista de sistemas con experiencia")
    assert len(result.experiences) == 3 and len(result.educations) == 2
    assert result.experiences[0]["company"] == "Empresa Uno SAS"
    assert result.experiences[0]["start_date"] == "2019-07"
    assert result.experiences[2]["end_date"] == "2019-02"
    assert result.educations[0]["institution"] == "Universidad de Prueba"
    assert result.educations[0]["start_year"] == "2020" and result.educations[0]["is_current"]
    assert result.educations[1]["end_year"] == "2019"
    assert all("Preferencias" not in item["degree"] for item in result.educations)


def test_title_period_parser_also_works_without_an_education_section():
    result = text_processor.analyze_cv(CV.split("Formación académica")[0])
    assert len(result.experiences) == 3 and not result.educations
