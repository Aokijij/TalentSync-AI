from types import SimpleNamespace as Row

from app.domain.services.career_learning import profile_areas
from app.domain.services.learning_relevance import ranked_resources


def test_project_functions_route_to_project_courses_before_generic_resources():
    profile = Row(
        profession="Analista de Proyectos",
        skills=[],
        experiences=[
            {
                "role": "Analista",
                "description": "Planeación de proyectos, seguimiento presupuestal y control de riesgos. Gestión documental e indicadores de desempeño.",
            }
        ],
    )
    resources = [
        {
            "id": "generic",
            "title": "Redacción de currículum",
            "skills": ["busqueda de empleo"],
            "category": "general",
        },
        {
            "id": "projects",
            "title": "Gestión de proyectos",
            "skills": ["gestión de proyectos", "planificación", "gestión de riesgos"],
            "category": "administration",
        },
        {
            "id": "python",
            "title": "Python avanzado",
            "skills": ["python"],
            "category": "technology",
        },
    ]
    areas = profile_areas(profile)
    assert "administration" in areas
    result = ranked_resources(resources, profile, areas)
    assert result[0]["id"] == "projects" and result[0]["relevance"]["kind"] == "context"
    assert "proyectos" in result[0]["relevance"]["reasons"][0]
    assert result[-1]["relevance"]["score"] == 0
    assert profile.skills == []


def test_declared_skills_rank_across_categories_and_sponsorship_has_no_effect():
    profile = Row(profession="Auxiliar", skills=["Excel"], experiences=[])
    resources = [
        {
            "id": "excel",
            "title": "Excel para informes",
            "skills": ["excel"],
            "category": "technology",
        },
        {
            "id": "generic",
            "title": "Curso administrativo",
            "skills": ["administracion"],
            "category": "administration",
            "sponsored": True,
        },
    ]
    ranked = ranked_resources(resources, profile, ["administration"])
    assert ranked[0]["id"] == "excel"
    assert "excel" in ranked[0]["relevance"]["reasons"][0]
    resources[0]["sponsored"] = True
    assert [
        row["relevance"]
        for row in ranked_resources(resources, profile, ["administration"])
    ] == [row["relevance"] for row in ranked]


def test_software_projects_alone_do_not_imply_project_management():
    profile = Row(
        profession="Desarrollador React",
        skills=["react"],
        experiences=[
            {"description": "Construí proyectos personales con React y JavaScript."}
        ],
    )
    assert "administration" not in profile_areas(profile)


def test_empty_profile_is_explicit_complementary_fallback():
    result = ranked_resources(
        [
            {
                "id": "general",
                "title": "Comunicación",
                "skills": ["comunicacion"],
                "category": "general",
            }
        ],
        Row(skills=[]),
        ["general"],
    )
    assert result[0]["relevance"]["kind"] == "complementary"
