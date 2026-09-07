from app.infrastructure.nlp import pdf_reader


def test_regular_extraction_is_used_when_layout_mode_is_empty(monkeypatch):
    class FakePage:
        def extract_text(self, extraction_mode=None):
            return "" if extraction_mode == "layout" else "Texto recuperado del CV"

    class FakeReader:
        def __init__(self, _file_path):
            self.pages = [FakePage()]

    monkeypatch.setattr(pdf_reader, "PdfReader", FakeReader)
    monkeypatch.setattr(pdf_reader, "_extract_docling_text", lambda _file_path: "")

    assert pdf_reader.extract_pdf_text("cv.pdf") == "Texto recuperado del CV"


def test_docling_enriches_difficult_pdf_and_keeps_native_fallback(monkeypatch):
    monkeypatch.setattr(
        pdf_reader, "_extract_pypdf_text", lambda _file_path: "Texto corto"
    )
    monkeypatch.setattr(
        pdf_reader,
        "_extract_docling_text",
        lambda _file_path: "# Experiencia\nContenido OCR",
    )
    monkeypatch.setattr(pdf_reader.settings, "cv_parser", "auto")

    result = pdf_reader.extract_pdf_text("cv.pdf")

    assert result.startswith("# Experiencia\nContenido OCR")
    assert result.endswith("PYPDF FALLBACK\nTexto corto")
