from textwrap import dedent

from app.domain.services.matching import combined_match
from app.infrastructure.nlp.text_processor import text_processor


def test_text_processor_extracts_skills_and_similarity():
    profile = text_processor.analyze("Desarrollador Python con React, SQL y FastAPI")
    job = text_processor.analyze("Vacante backend Python FastAPI con PostgreSQL")

    assert "python" in profile.skills
    assert text_processor.similarity_percentage(profile.embedding, job.embedding) > 0


def test_extracts_cross_sector_skills_from_short_job_catalog_summaries():
    software = text_processor.analyze_job(
        "Desarrollador de Software Full Stack. Dominio de Java, .NET, inteligencia artificial y analítica de datos."
    )
    education = text_processor.analyze_job(
        "Docente de Matemáticas con conocimientos pedagógicos y experiencia en enseñanza."
    )
    operations = text_processor.analyze_job(
        "Auxiliar de bodega para logística, despachos y control de inventarios."
    )

    assert {
        "desarrollo de software",
        "java",
        ".net",
        "inteligencia artificial",
        "analítica de datos",
    } <= set(software.skills)
    assert {"docencia", "matemáticas", "pedagogía"} <= set(education.skills)
    assert {"logística", "despachos", "gestión de inventarios"} <= set(
        operations.skills
    )


def test_extracts_environmental_cv_with_professional_experience_format():
    cv = """
    Ingeniera ambiental
    Mis estudios
    POSGRADO / ESPECIALIZACIÓN EN SEGURIDAD Y SALUD EN EL TRABAJO
    UNIVERSIDAD ECCI
    Junio 2022 - Febrero 2024
    Experiencia profesional
    RESIDENTE AMBIENTAL
    CONSTRUCTORA EJEMPLO SAS
    FUNCIONES: Gestión ambiental, seguimiento ambiental, manejo de residuos, informes técnicos y cumplimiento de la normatividad ambiental.
    Enero 2020 - Agosto 2023
    Contacto: 300 000 0000
    """

    result = text_processor.analyze_cv(dedent(cv))

    assert result.profession == "Ingeniera Ambiental"
    assert result.phone == "300 000 0000"
    assert len(result.experiences) == 1
    assert result.experiences[0]["company"] == "CONSTRUCTORA EJEMPLO SAS"
    assert len(result.educations) == 1
    assert "gestión ambiental" in result.skills
    assert "manejo de residuos" in result.skills
    assert "informes técnicos" in result.skills


def test_match_prioritizes_required_skill_coverage():
    assert combined_match(30, 100) == 72


def test_extracts_spaced_multicolumn_cv_timeline():
    cv = """
    E D U C A C I Ó N
    P R A C T I C A N T E  D E  I N G E N I E R Í A  D E  S I S T E M A S  |
    E X P E R I E N C I A  L A B O R A L
    2 0 1 8  -  2 0 1 9
    Pragma S . A .
    D E S A R R O L L A D O R  F R O N T - E N D
    Desarrollo y mantenimiento de interfaces web.
    Integración y consumo de APIs REST.
    2 0 1 9  -  2 0 2 0
    Paralelo 360 SAS
    A N A L I S T A  D E  R E Q U E R I M I E N T O S  Y  Q A
    Ejecución de pruebas funcionales y documentación de incidencias.
    2 0 2 2  -  2 0 2 3
    Ricoh
    A N A L I S T A  D E  I N V E N T A R I O
    Gestión y control de inventarios mediante herramientas tecnológicas.
    P E R F I L  P R O F E S I O N A L
    UNIVERSIDAD CATÓLICA LUIS AMIGÓ
    I n g e n i e r í a  d e  S i s t e m a s  e  I n f o r m á t i c a
    2 0 2 0  -  P r e s e n t e
    2 0 1 7  -  2 0 1 9
    SENA
    T e c n ó l o g o  e n  A n á l i s i s  y  D e s a r r o l l o  d e  S i s t e m a s  d e  I n f o r m a c i ó n
    """

    result = text_processor.analyze_cv(dedent(cv))

    assert result.profession == "Practicante De Ingeniería De Sistemas"
    assert len(result.experiences) == 3
    assert {item["company"] for item in result.experiences} == {
        "Pragma S.A.",
        "Paralelo 360 SAS",
        "Ricoh",
    }
    assert all(item["description"] for item in result.experiences)
    assert len(result.educations) == 2
    assert {item["institution"] for item in result.educations} == {
        "UNIVERSIDAD CATÓLICA LUIS AMIGÓ",
        "SENA",
    }


def test_extracts_docling_markdown_education_without_crossing_entries():
    cv = """
    ## EDUCACIÓN
    2020 - Presente
    ## UNIVERSIDAD CATÓLICA LUIS AMIGÓ
    Ingeniería de Sistemas e Informática
    2017 - 2019
    SENA
    Tecnólogo en Análisis y Desarrollo de Sistemas de Información
    ## HABILIDADES
    Python
    """

    result = text_processor.analyze_cv(dedent(cv))

    assert len(result.educations) == 2
    assert result.educations[0]["start_year"] == "2020"
    assert result.educations[0]["end_year"] == "Presente"
    assert result.educations[1]["institution"] == "SENA"


def test_extracts_labelled_docling_resume_without_using_visual_positions():
    cv = """
    ## FORMACIÓN ACADÉMICA

    ## Pregrado: Construcciones Civiles - Décimo semestre (En curso)

    - Tecnóloga: Construcción de Edificaciones - 2019
    - Técnica: Construcción y Diseño de Edificaciones - 2015
    - Bachiller:

    I.E. Colegio de Ejemplo - 2015

    ## Cursos y diplomados:
    - AutoCAD

    ## EXPERIENCIA LABORAL

    ## Empresa Constructora Alfa (Enero 2023 - Mayo 2024)

    Cargo: Residente Administrativo.
    Jefe inmediato: Persona de contacto - Celular: 3000000000

    ## Funciones:
    - Controlar documentación y presupuesto.
    - Gestionar compras y proveedores.

    ## Consultores Beta S.A.S. (Junio 2021 - Diciembre 2022)

    Puesto: Inspector Técnico

    ## Responsabilidades
    - Supervisión técnica y control de calidad.

    ## HABILIDADES
    AutoCAD
    """

    result = text_processor.analyze_cv(dedent(cv))

    assert [item["company"] for item in result.experiences] == [
        "Empresa Constructora Alfa",
        "Consultores Beta S.A.S.",
    ]
    assert result.experiences[0]["role"] == "Residente Administrativo"
    assert "Gestionar compras" in result.experiences[0]["description"]
    assert result.experiences[1]["role"] == "Inspector Técnico"
    assert "control de calidad" in result.experiences[1]["description"]
    assert len(result.educations) == 4
    assert result.educations[0]["end_year"] == "Presente"
    assert result.educations[-1]["degree"] == "Bachiller"
    assert result.educations[-1]["institution"] == "I.E. Colegio de Ejemplo"
