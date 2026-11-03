# ruff: noqa: F811
from test_api_flows import client, register  # noqa: F401

from app.infrastructure.nlp import resumes


def test_upload_stores_extracted_months_and_reimport_preserves_them(
    client, monkeypatch, tmp_path
):
    from app.core.config import settings

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    _, candidate = register(client, "month-cv-person", profession="Analista")
    text = "EXPERIENCIA LABORAL\nEmpresa Ejemplo (Julio 2025 – Noviembre 2025)\nCargo: Analista de Proyectos\nFunciones:\nPlaneación y seguimiento de proyectos.\n"
    monkeypatch.setattr(resumes, "extract_pdf_text", lambda _: text)
    for _ in range(2):
        response = client.post(
            "/api/v1/profiles/me/cv",
            headers=candidate,
            files={"file": ("cv.pdf", b"%PDF-test", "application/pdf")},
        )
        assert response.status_code == 200, response.text
        rows = response.json()["experiences"]
        assert len(rows) == 1
        assert rows[0]["start_date"] == "2025-07" and rows[0]["end_date"] == "2025-11"
    saved = client.get("/api/v1/profiles/me", headers=candidate).json()
    assert saved["experiences"][0]["start_date"] == "2025-07"
