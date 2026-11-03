import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.infrastructure.nlp import pdf_reader


def test_mixed_pdf_routes_scanned_page_to_ocr_despite_good_first_page(monkeypatch):
    class Page:
        def __init__(self, text, images): self.text, self.images = text, images
        def extract_text(self, **kwargs): return self.text
    monkeypatch.setattr(pdf_reader, "PdfReader", lambda _: SimpleNamespace(pages=[Page("Experiencia Python " * 30, []), Page("", [object()])]))
    monkeypatch.setattr(pdf_reader.settings, "cv_parser", "auto")
    monkeypatch.setattr(pdf_reader, "_extract_docling_text", lambda _: "Experiencia Python\nFormación recuperada del escaneo")
    assert "Formación recuperada" in pdf_reader.extract_pdf_text("mixed.pdf")


def test_pdf_page_limit_is_not_silently_truncated_or_sent_to_ocr(monkeypatch):
    monkeypatch.setattr(pdf_reader, "PdfReader", lambda _: SimpleNamespace(pages=[object()] * 21))
    monkeypatch.setattr(pdf_reader, "_extract_docling_text", lambda _: pytest.fail("Oversized CV must be rejected"))
    with pytest.raises(pdf_reader.PDFLimitError): pdf_reader.extract_pdf_text("long.pdf")


def test_broken_native_layer_can_still_be_recovered_by_ocr(monkeypatch):
    monkeypatch.setattr(pdf_reader.settings, "cv_parser", "auto")
    def fail(_): raise ValueError("private document diagnostic")
    monkeypatch.setattr(pdf_reader, "_extract_pypdf_text", fail)
    monkeypatch.setattr(pdf_reader, "_extract_docling_text", lambda _: "Texto recuperado")
    assert pdf_reader.extract_pdf_text("damaged.pdf") == "Texto recuperado"


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


def test_isolated_ocr_keeps_credentials_out_of_child_and_returns_text(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf_reader.settings, "cv_docling_python", sys.executable)
    monkeypatch.setenv("GMAIL_MAIL_REFRESH_TOKEN", "private-token")
    monkeypatch.setenv("DATABASE_URL", "private-database")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "private-storage")
    monkeypatch.setenv("HF_HOME", str(tmp_path))

    def run(args, **options):
        assert args[0] == sys.executable
        assert not any(key in options["env"] for key in ["DATABASE_URL", "GMAIL_MAIL_REFRESH_TOKEN", "R2_SECRET_ACCESS_KEY"])
        assert options["env"]["HF_HOME"] == str(tmp_path)
        assert options["env"]["HF_HUB_OFFLINE"] == "1"
        assert json.loads(options["input"])["path"] == str((tmp_path / "cv.pdf").resolve())
        return SimpleNamespace(returncode=0, stdout=json.dumps({"text": "  Texto OCR  "}))

    monkeypatch.setattr(pdf_reader.subprocess, "run", run)
    assert pdf_reader._extract_docling_text(str(tmp_path / "cv.pdf")) == "Texto OCR"


def test_isolated_ocr_timeout_or_malformed_result_keeps_native_text(monkeypatch):
    monkeypatch.setattr(pdf_reader.settings, "cv_docling_python", sys.executable)
    monkeypatch.setattr(pdf_reader.settings, "cv_parser", "auto")
    monkeypatch.setattr(pdf_reader, "_extract_pypdf_text", lambda _: "Texto nativo")

    def timeout(*args, **_options):
        raise subprocess.TimeoutExpired(args[0], 45)

    monkeypatch.setattr(pdf_reader.subprocess, "run", timeout)
    assert pdf_reader.extract_pdf_text("cv.pdf") == "Texto nativo"
    monkeypatch.setattr(pdf_reader.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout='{"text":123}'))
    assert pdf_reader.extract_pdf_text("cv.pdf") == "Texto nativo"
