# ruff: noqa: F811
from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfReader
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


def test_export_includes_only_owner_evidence_when_selected(client):
    owner, headers = register(client, "evidence-owner")
    other, _ = register(client, "evidence-other")
    with client.session_factory() as db:
        db.get(User, owner["id"]).profile.evidence = [{"title": "Proyecto del candidato", "description": "Análisis documentado de pedidos"}]
        db.get(User, other["id"]).profile.evidence = [{"title": "Proyecto privado de otra cuenta"}]
        db.commit()
    included = text(client.post("/api/v1/profiles/me/export", headers=headers, json={"sections": ["evidence"]}))
    omitted = text(client.post("/api/v1/profiles/me/export", headers=headers, json={"sections": []}))
    assert "Muestras de trabajo" in included and "Análisis documentado de pedidos" in included
    assert "otra cuenta" not in included and "Proyecto del candidato" not in omitted


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
