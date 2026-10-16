# ruff: noqa: F811
from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from test_api_flows import client, company_account, register  # noqa: F401

from app.infrastructure.database.models import User


def text(response):
    assert response.status_code == 200, response.text
    return " ".join(page.extract_text() for page in PdfReader(BytesIO(response.content)).pages)


@pytest.mark.parametrize("style", ["classic", "modern", "minimal"])
def test_preview_honors_sections_without_saving_profile_or_leaking_contacts(client, style):
    user, headers = register(client, f"export-{style}", profession="Diseñadora gráfica", skills=["habilidad-marcador"])
    with client.session_factory() as db:
        db.get(User, user["id"]).profile.experience = "Resumen con acentos: comunicación."
        db.commit()
    before = client.get("/api/v1/profiles/me", headers=headers).json()
    payload = {"sections": ["summary"], "include_photo": False, "profile": {**before, "name": "Nombre en borrador", "resume_style": style, "resume_color": "teal"}}
    # Response-only properties are ignored by the existing ProfileUpdate contract.
    response = client.post("/api/v1/profiles/me/export", headers=headers, json=payload)
    contents = text(response)
    assert "Nombre en borrador" in contents and "comunicación" in contents
    assert "Habilidades" not in contents and "habilidad-marcador" not in contents and user["email"] not in contents
    assert client.get("/api/v1/profiles/me", headers=headers).json() == before
    assert client.get("/api/v1/auth/me", headers=headers).json()["name"] == user["name"]
    assert "inline" in response.headers["content-disposition"] and "no-store" in response.headers["cache-control"]


def test_export_validates_options_and_is_candidate_private(client):
    _, headers = register(client, "export-private")
    _, company = company_account(client, "export-company")
    assert client.post("/api/v1/profiles/me/export", json={}).status_code == 401
    assert client.post("/api/v1/profiles/me/export", headers=company, json={}).status_code == 403
    for data in [{"sections": ["cv_text"]}, {"user_id": 555}, {"profile": {"resume_style": "unknown"}}]:
        assert client.post("/api/v1/profiles/me/export", headers=headers, json=data).status_code == 422


@pytest.mark.parametrize("style", ["classic", "modern", "minimal"])
def test_export_orders_experiences_and_keeps_modern_skill_levels(client, style):
    _, headers = register(client, f"ordered-{style}", skills=["python"])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile.update(resume_style=style, skill_levels={"python": "advanced"}, experiences=[
        {"role": "Cargo anterior marcador", "start_date": "2018-01", "end_date": "2019-01"},
        {"role": "Cargo reciente marcador", "start_date": "2022-01", "end_date": "2023-01"},
        {"role": "Cargo actual marcador", "start_date": "2024-01", "is_current": True},
    ])
    contents = text(client.post("/api/v1/profiles/me/export", headers=headers, json={"profile": profile}))
    assert contents.index("Cargo actual marcador") < contents.index("Cargo reciente marcador") < contents.index("Cargo anterior marcador")
    assert "Avanzado" in contents
    if style == "modern":
        assert "python (Avanzado)" not in contents


def test_export_includes_only_owner_evidence_when_selected(client):
    owner, headers = register(client, "evidence-owner")
    other, _ = register(client, "evidence-other")
    with client.session_factory() as db:
        db.get(User, owner["id"]).profile.evidence = [{"title": "Proyecto del candidato", "description": "Análisis documentado de pedidos"}]
        db.get(User, other["id"]).profile.evidence = [{"title": "Proyecto privado de otra cuenta"}]
        db.commit()
    included = text(client.post("/api/v1/profiles/me/export", headers=headers, json={"sections": ["evidence"]}))
    omitted = text(client.post("/api/v1/profiles/me/export", headers=headers, json={"sections": []}))
    assert "proyectos y logros" in included.lower() and "Análisis documentado de pedidos" in included
    assert "otra cuenta" not in included and "Proyecto del candidato" not in omitted


@pytest.mark.parametrize("include_photo", [False, True])
def test_modern_header_keeps_a_long_name_within_two_lines_and_inside_the_page(client, include_photo):
    _, headers = register(client, "modern-header")
    name = "María Alejandra Restrepo Gómez Delgado"
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={
        "sections": ["contact"], "include_photo": include_photo,
        "profile": {"name": name, "resume_style": "modern", "profession": "Desarrolladora de aplicaciones web",
                    "phone": "+57 300 123 4567", "location": "Medellín", "department": "Antioquia"},
    })
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 1
    names = []

    def visit(value, cm, tm, font, size):
        if size >= 20 and value.strip():
            names.append((value.strip(), cm[4] + tm[4], cm[5] + tm[5], size))

    contents = reader.pages[0].extract_text(visitor_text=visit)
    assert name in " ".join(contents.split())
    assert "+57 300 123 4567" in contents and "Medellín" in contents
    assert len({round(item[2]) for item in names}) <= 2
    for value, x, y, size in names:
        assert x >= 38 and y > 650
        assert x + pdfmetrics.stringWidth(value, "ResumeBold", size) <= 557


@pytest.mark.parametrize("style", ["classic", "modern", "minimal"])
def test_reference_designs_keep_contact_on_the_right_and_distinguish_columns_and_typefaces(client, style):
    user, headers = register(client, "design-" + style)
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={"profile": {
        "name": "Jose", "resume_style": style, "skills": ["habilidad de ejemplo"],
        "experiences": [{"role": "Cargo marcador", "company": "Empresa de ejemplo", "start_date": "2023-01", "end_date": "2024-01"}],
        "educations": [{"degree": "Título de ejemplo", "institution": "Institución", "start_year": "2018", "end_year": "2022"}],
    }})
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    locations = {}

    def visit(value, cm, tm, font, size):
        for marker in ("Jose", user["email"], "Cargo marcador"):
            if marker in value:
                locations[marker] = (cm[4] + tm[4], str(font.get("/BaseFont", "")))

    reader.pages[0].extract_text(visitor_text=visit)
    assert locations[user["email"]][0] >= 425
    assert ("Times-Roman" in locations["Jose"][1]) == (style == "minimal")
    assert (locations["Cargo marcador"][0] < 100) == (style == "minimal")


@pytest.mark.parametrize("color", ["default", "forest", "wine", "blue"])
def test_modern_color_themes_export_real_gradients_without_losing_skill_names_or_levels(client, color):
    _, headers = register(client, "modern-gradient-" + color)
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={"profile": {
        "name": "Nombre de ejemplo", "resume_style": "modern", "resume_color": color,
        "skills": ["css", "aseguramiento de calidad"],
        "skill_levels": {"css": "basic", "aseguramiento de calidad": "advanced"},
    }})
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    contents = " ".join(page.extract_text() for page in reader.pages)
    assert "css" in contents and "Básico" in contents
    assert "aseguramiento de calidad" in contents and "Avanzado" in contents
    shadings = reader.pages[0]["/Resources"]["/Shading"].get_object()
    assert len(shadings) >= 2  # Sidebar and avatar retain actual vector gradients.
    for reference in shadings.values():
        shading = reference.get_object()
        assert shading["/ShadingType"] == 2
        function = shading["/Function"].get_object()
        assert function["/C0"] != function["/C1"]


@pytest.mark.parametrize("style", ["classic", "modern", "minimal"])
def test_long_profiles_keep_last_skill_and_experience_across_pages(client, style):
    _, headers = register(client, f"long-{style}", skills=[f"habilidad-marcador-{index}" for index in range(80)])
    profile = client.get("/api/v1/profiles/me", headers=headers).json()
    profile.update(resume_style=style, experiences=[{"role": f"Cargo marcador {index}", "company": "Organización de prueba", "start_date": "2020-01", "end_date": "2021-01", "description": "Preparación de entregables y documentación de actividades. " * 8} for index in range(12)])
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={"profile": profile})
    contents = text(response)
    assert "habilidad-marcador-79" in contents and "Cargo marcador 11" in contents
    assert len(PdfReader(BytesIO(response.content)).pages) > 1


def test_modern_sidebar_does_not_create_an_extra_page_just_for_preferences(client):
    _, headers = register(client, "modern-sidebar")
    # A typical sidebar leaves room for readable spacing, languages and courses.
    skills = ["automatización", "css", "desarrollo de software", "git", "html", "qa", "react", "testing", "fastapi", "javascript", "python", "vite", "sql", "typescript"]
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={"profile": {
        "name": "María Alejandra Restrepo Gómez Delgado", "profession": "Desarrolladora Front-End", "resume_style": "modern",
        "experience": "Resumen marcador que debe conservarse.",
        "experiences": [{"role": "Cargo conservado", "start_date": "2022-01", "end_date": "2023-01"}],
        "educations": [{"degree": "Formación conservada", "institution": "Institución", "start_year": "2018", "end_year": "2022"}],
        "skills": skills, "skill_levels": {skill: "intermediate" for skill in skills},
        "links": [{"platform": "github", "url": "https://github.com/example-person"}, {"platform": "linkedin", "url": "https://linkedin.com/in/example-person"}],
        "languages": [{"name": "español", "level": "NATIVE"}, {"name": "inglés", "level": "B1"}],
        "certifications": [{"name": "Excel básico", "issuer": "Entidad de formación", "year": "2017"}],
        "preferred_sector": "Tecnología y software", "preferred_modality": "remote", "availability": "immediate",
    }})
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 1
    contents = reader.pages[0].extract_text()
    for marker in (*skills, "Cargo conservado", "Formación conservada", "Resumen marcador", "Excel básico", "Tecnología y software", "Remoto", "Inmediata"):
        assert marker in contents


def test_minimal_education_cards_split_across_pages_without_losing_long_descriptions(client):
    _, headers = register(client, "minimal-long-card")
    response = client.post("/api/v1/profiles/me/export", headers=headers, json={"sections": ["educations"], "profile": {
        "resume_style": "minimal", "educations": [{"degree": "Título de prueba", "institution": "Institución",
            "start_year": "2018", "end_year": "2022", "description": "Inicio del contenido. " + "Descripción de la formación y los proyectos realizados. " * 150 + "Fin del contenido."}],
    }})
    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) > 1
    contents = " ".join(page.extract_text() for page in reader.pages)
    assert "Inicio del contenido." in contents and "Fin del contenido." in contents


def test_photo_is_owner_scoped_and_can_be_omitted(client, monkeypatch, tmp_path):
    from app.core.config import settings
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    _, a = register(client, "photo-owner")
    _, b = register(client, "photo-other")
    image = BytesIO(); Image.new("RGB", (100, 100), "#123456").save(image, format="PNG")
    client.post("/api/v1/profiles/me/photo", headers=a, files={"file": ("portrait.png", image.getvalue(), "image/png")}).raise_for_status()
    def images(response):
        assert response.status_code == 200, response.text
        return sum(len(page.images) for page in PdfReader(BytesIO(response.content)).pages)
    assert images(client.post("/api/v1/profiles/me/export", headers=a, json={"include_photo": True})) == 1
    assert images(client.post("/api/v1/profiles/me/export", headers=a, json={"include_photo": False})) == 0
    assert images(client.post("/api/v1/profiles/me/export", headers=b, json={"include_photo": True})) == 0
