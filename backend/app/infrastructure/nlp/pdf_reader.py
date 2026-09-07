from __future__ import annotations

import logging
import re
from functools import lru_cache

from pypdf import PdfReader

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _docling_converter():
    """Build Docling lazily so startup stays fast and lite installs still work."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        EasyOcrOptions,
        OcrMode,
        PdfPipelineOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = settings.cv_ocr_enabled
    pipeline_options.do_table_structure = False
    pipeline_options.document_timeout = settings.cv_docling_timeout_seconds
    if settings.cv_ocr_enabled:
        mode = (
            OcrMode.FULL_PAGE
            if settings.cv_ocr_force_full_page
            else OcrMode.PDF_AWARE_LAYOUT_REGIONS
        )
        pipeline_options.ocr_options = EasyOcrOptions(lang=["es", "en"], mode=mode)

    return DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        },
    )


def _extract_docling_text(file_path: str) -> str:
    try:
        result = _docling_converter().convert(file_path)
        return (result.document.export_to_markdown() or "").strip()
    except ImportError:
        logger.info("Docling no está instalado; se usa el extractor pypdf.")
    except Exception:
        logger.exception(
            "Docling no pudo procesar %s; se usa el extractor pypdf.", file_path
        )
    return ""


def _needs_advanced_parser(text: str) -> bool:
    plain_text = text.replace("COORDINATE EXPERIENCE LAYOUT", "").strip()
    if len(plain_text) < settings.cv_docling_min_text_chars:
        return True
    if "COORDINATE EXPERIENCE LAYOUT" in text:
        return True
    return plain_text.count("�") / max(len(plain_text), 1) > 0.02


def _coordinate_experience_layout(page) -> str:
    """Recover employment blocks from PDFs whose form objects lose reading order."""
    fragments: list[tuple[float, float, str]] = []

    def visitor(text, cm, tm, _font, _size) -> None:
        value = (text or "").strip()
        # pypdf may emit a final aggregate fragment in addition to the positioned
        # fragments. Keeping it would duplicate the whole page.
        if not value or value.count("\n") > 3:
            return
        try:
            x = float(tm[4]) * float(cm[0]) + float(tm[5]) * float(cm[2]) + float(cm[4])
            y = float(tm[4]) * float(cm[1]) + float(tm[5]) * float(cm[3]) + float(cm[5])
        except (IndexError, TypeError, ValueError):
            return
        # Some nested PDF form objects are emitted twice: once at their local
        # origin and once at the real page position. Discard the local copy.
        if x < 100 and y < 200:
            return
        fragments.append((x, y, value))

    try:
        page.extract_text(visitor_text=visitor)
    except (TypeError, ValueError):
        return ""
    if len(fragments) < 5:
        return ""

    unique: list[tuple[float, float, str]] = []
    seen = set()
    for x, y, value in fragments:
        key = (round(x, 1), round(y, 1), value)
        if key not in seen:
            seen.add(key)
            unique.append((x, y, value))

    # Detect a true column boundary using the largest horizontal gap. Dates can
    # be right-aligned far from the job title, so require both sides to contain
    # several fragments before accepting a split.
    anchors = sorted(set(round(x, 0) for x, _, _ in unique))
    columns = [unique]
    if len(anchors) >= 4:
        gaps = [
            (anchors[index + 1] - anchors[index], index)
            for index in range(len(anchors) - 1)
        ]
        gap, index = max(gaps)
        span = max(anchors[-1] - anchors[0], 1)
        threshold = (anchors[index] + anchors[index + 1]) / 2
        left = [item for item in unique if item[0] <= threshold]
        right = [item for item in unique if item[0] > threshold]
        if gap / span >= 0.16 and len(left) >= 5 and len(right) >= 5:
            columns = [left, right]

    def ordered_text(column: list[tuple[float, float, str]]) -> str:
        def key(item: tuple[float, float, str]) -> tuple[float, float]:
            x, y, value = item
            # Right-aligned date ranges belong to the same row as the company;
            # place them just before it to produce period -> company -> role.
            is_period = bool(re.search(r"(?:19|20)\s*\d\s*\d\s*\d\s*[-–—]", value))
            return (y - 15 if is_period else y, x)

        return "\n".join(value for _, _, value in sorted(column, key=key))

    candidates = [ordered_text(column) for column in columns]
    employment_columns = [
        value
        for value in candidates
        if "EXPERIENCIA" in value.upper()
        and any(word in value.upper() for word in ("LABORAL", "PROFESIONAL", "WORK"))
    ]
    return "\n".join(employment_columns)


def _extract_pypdf_text(file_path: str) -> str:
    """Extract text from a PDF.

    Many CVs are image-based scans; in that case pypdf usually returns
    empty text per page.

    Returns an empty string if no extractable text is found.
    """

    reader = PdfReader(file_path)

    texts: list[str] = []
    for page in reader.pages:
        # Layout mode preserves columns, headings and CV timelines much better.
        # Some PDFs do not support it, so keep the regular extractor as fallback.
        used_regular_fallback = False
        try:
            page_text = page.extract_text(extraction_mode="layout") or ""
        except (TypeError, ValueError):
            page_text = page.extract_text() or ""
            used_regular_fallback = True
        # Some PDFs accept layout mode but silently return an empty string.
        # Their regular text layer can still be perfectly usable.
        if not page_text.strip():
            page_text = page.extract_text() or ""
            used_regular_fallback = True
        if used_regular_fallback and page_text.strip():
            coordinate_layout = _coordinate_experience_layout(page)
            if coordinate_layout.strip():
                page_text = (
                    f"{page_text}\n\nCOORDINATE EXPERIENCE LAYOUT\n{coordinate_layout}"
                )
        if page_text.strip():
            texts.append(page_text)

    return "\n".join(texts).strip()


def extract_pdf_text(file_path: str) -> str:
    """Extract a CV with pypdf plus an optional Docling/OCR fallback.

    ``CV_PARSER=auto`` keeps ordinary text PDFs fast and routes scanned or
    structurally difficult documents through Docling. ``docling`` forces the
    advanced route, while ``pypdf`` disables it.
    """
    pypdf_text = _extract_pypdf_text(file_path)
    parser = settings.cv_parser.strip().lower()
    if parser not in {"auto", "pypdf", "docling"}:
        logger.warning("CV_PARSER=%s no es válido; se usará auto.", settings.cv_parser)
        parser = "auto"

    should_use_docling = parser == "docling" or (
        parser == "auto" and _needs_advanced_parser(pypdf_text)
    )
    if not should_use_docling:
        return pypdf_text

    docling_text = _extract_docling_text(file_path)
    if not docling_text:
        return pypdf_text
    if not pypdf_text:
        return docling_text
    # Preserve the native text as evidence: one engine can recover a field that
    # the other omits, especially in heavily designed multi-column CVs.
    return f"{docling_text}\n\nPYPDF FALLBACK\n{pypdf_text}"
