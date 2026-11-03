"""Standalone OCR interpreter. One bounded local PDF in; JSON text out."""
import contextlib
import json
import os
import sys
from pathlib import Path


def convert(payload):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        EasyOcrOptions,
        OcrMode,
        PdfPipelineOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    path = Path(payload["path"])
    if not path.is_absolute() or not path.is_file() or path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Invalid local PDF")
    with path.open("rb") as stream:
        if not stream.read(5).startswith(b"%PDF-"):
            raise ValueError("Invalid local PDF")
    options = PdfPipelineOptions()
    artifacts = os.environ.get("DOCLING_ARTIFACTS_PATH")
    if artifacts:
        options.artifacts_path = Path(artifacts)
    options.do_table_structure = False
    options.enable_remote_services = False
    options.document_timeout = max(1, min(float(payload["timeout"]), 120))
    options.do_ocr = bool(payload["ocr"])
    if options.do_ocr:
        options.ocr_options = EasyOcrOptions(lang=["es", "en"],
            mode=OcrMode.FULL_PAGE if payload["force"] else OcrMode.PDF_AWARE_LAYOUT_REGIONS,
            download_enabled=False)
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
    return (converter.convert(path, max_num_pages=20).document.export_to_markdown() or "")[:100_000]


if __name__ == "__main__":
    try:
        payload = json.loads(sys.stdin.read(8192))
        with contextlib.redirect_stdout(sys.stderr):
            text = convert(payload)
        sys.stdout.write(json.dumps({"text": text}, ensure_ascii=False))
    except Exception:
        # The parent falls back to the native text layer; no private diagnostics.
        sys.stdout.write('{"text":""}')
        raise SystemExit(1) from None
