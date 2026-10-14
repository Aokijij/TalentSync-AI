"""Private, designed CVs. Preview and download use the same PDF bytes."""
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from PIL import Image as PillowImage
from PIL import ImageOps
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.application.errors import UseCaseError

SECTIONS = {"contact", "summary", "experiences", "educations", "certifications", "skills", "languages", "evidence", "preferences"}
PALETTES = {"forest": "#166534", "wine": "#881337", "slate": "#334155", "navy": "#1e3a8a", "blue": "#1d4ed8", "teal": "#0f766e", "rose": "#be185d"}


def date_label(value):
    value = str(value or "")
    if re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", value):
        year, month = value.split("-")
        return f"{['ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.', 'jul.', 'ago.', 'sep.', 'oct.', 'nov.', 'dic.'][int(month) - 1]} {year}"
    return value


@lru_cache(maxsize=1)
def fonts():
    folder = Path(reportlab.__file__).parent / "fonts"
    for name, filename in [("Resume", "Vera.ttf"), ("ResumeBold", "VeraBd.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(folder / filename)))
    pdfmetrics.registerFontFamily("Resume", normal="Resume", bold="ResumeBold", italic="Resume", boldItalic="ResumeBold")


def resume_pdf(user, *, sections=None, include_photo=True, photo=None):
    fonts()
    profile = user.profile
    included = SECTIONS if sections is None else set(sections) & SECTIONS
    layout = profile.resume_style or "classic"
    accent = colors.HexColor(PALETTES.get(profile.resume_color, {"classic": "#0c4a6e", "modern": "#4338ca", "minimal": "#0f172a"}.get(layout, "#0c4a6e")))
    ink, muted, line = [colors.HexColor(value) for value in ("#172a3a", "#526477", "#dce4eb")]
    base = ParagraphStyle("CVBody", parent=getSampleStyleSheet()["Normal"], fontName="Resume", fontSize=9, leading=14, textColor=ink, spaceAfter=7, splitLongWords=True)
    heading = ParagraphStyle("CVHeading", parent=base, fontName="ResumeBold", fontSize=12, leading=16, textColor=accent, spaceBefore=15, spaceAfter=6, keepWithNext=True)
    role = ParagraphStyle("CVRole", parent=base, fontName="ResumeBold", fontSize=10, leading=15, spaceBefore=8, spaceAfter=3, keepWithNext=True)
    meta = ParagraphStyle("CVMeta", parent=base, fontSize=8, leading=12, textColor=muted, spaceAfter=6)
    inverse = layout == "classic"
    name_style = ParagraphStyle("CVName", parent=base, fontName="ResumeBold", fontSize=23 if layout != "minimal" else 21, leading=29, textColor=colors.white if inverse else ink, spaceAfter=7)
    profession_style = ParagraphStyle("CVProfession", parent=base, fontSize=11, leading=16, textColor=colors.white if inverse else accent, spaceAfter=7)
    contact_style = ParagraphStyle("CVContact", parent=meta, textColor=colors.HexColor("#e0f2fe") if inverse else muted, leading=13, spaceAfter=0)

    def paragraph(value, style=base):
        return Paragraph(escape(str(value or "")).replace("\n", "<br/>"), style)

    identity = [paragraph(user.name, name_style)]
    if profile.profession and len(profile.profession) <= 250:
        identity.append(paragraph(profile.profession, profession_style))
    if "contact" in included:
        contact = [user.email, getattr(profile, "phone", None), ", ".join(filter(None, [getattr(profile, "location", None), getattr(profile, "department", None)]))]
        contact_text = " · ".join(str(value) for value in contact if value)
        if len(contact_text) <= 450:
            identity.append(paragraph(contact_text, contact_style))
    photo_flowable = None
    if include_photo and photo:
        try:
            with PillowImage.open(BytesIO(photo)) as original:
                if original.width * original.height > 20_000_000:
                    raise ValueError("Photo too large to decode")
                image = ImageOps.fit(ImageOps.exif_transpose(original).convert("RGB"), (320, 320))
                image_data = BytesIO(); image.save(image_data, format="JPEG", quality=92)
            image_data.seek(0)
            photo_flowable = Image(image_data, width=76, height=76)
        except (OSError, ValueError, PillowImage.DecompressionBombError):
            raise UseCaseError(status_code=422, detail="No pudimos incluir la foto. Reemplázala o desactiva Foto para exportar") from None
    header = Table([[identity, photo_flowable]] if photo_flowable else [[identity]], colWidths=[381, 118] if photo_flowable else [499])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 18), ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 20), ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("BACKGROUND", (0, 0), (-1, -1), accent if inverse else colors.HexColor("#f1f5f9") if layout == "modern" else colors.white),
        ("LINEBELOW", (0, 0), (-1, -1), 2 if layout != "minimal" else .7, accent),
    ]))
    story = [header, Spacer(1, 6)]
    if profile.profession and len(profile.profession) > 250:
        story.append(paragraph(profile.profession))
    if "contact" in included and len(contact_text) > 450:
        story.append(paragraph(contact_text, meta))

    def section(title):
        rule = HRFlowable(width="100%", thickness=.5, color=line, spaceAfter=7)
        rule.keepWithNext = True
        story.extend([paragraph(title, heading), rule])

    if "summary" in included and profile.experience:
        section("Perfil profesional"); story.append(paragraph(profile.experience))
    for title, key, fields in [("Experiencia laboral", "experiences", ["role", "company"]), ("Formación académica", "educations", ["degree", "institution"]), ("Cursos y certificaciones", "certifications", ["name", "issuer"]), ("Muestras de trabajo", "evidence", ["title"])]:
        items = getattr(profile, key, None) or []
        if key not in included or not items:
            continue
        section(title)
        for item in items:
            story.append(paragraph(" · ".join(str(item.get(field) or "") for field in fields if item.get(field)), role))
            ongoing = "En curso" if key == "educations" else "Actualidad"
            dates = [item.get("start_date") or item.get("start_year"), ongoing if item.get("is_current") else item.get("end_date") or item.get("end_year") or item.get("year")]
            if any(dates):
                story.append(paragraph(" - ".join(date_label(value) for value in dates if value), meta))
            if item.get("description"):
                story.append(paragraph(item["description"]))
    if "educations" in included and not getattr(profile, "educations", None) and profile.education:
        section("Formación académica"); story.append(paragraph(profile.education))
    if "skills" in included and profile.skills:
        section("Habilidades"); story.append(paragraph(" · ".join(profile.skills)))
    if "languages" in included and profile.languages:
        section("Idiomas"); story.append(paragraph(" · ".join(f"{item.get('name', item.get('language', ''))}: {'Nativo' if item.get('level') == 'NATIVE' else item.get('level', '')}" for item in profile.languages)))
    if "preferences" in included:
        labels = {"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial", "immediate": "Inmediata", "two_weeks": "En 15 días", "one_month": "En 30 días", "negotiable": "Fecha acordada"}
        values = [getattr(profile, "preferred_sector", None), labels.get(getattr(profile, "preferred_modality", None)), labels.get(getattr(profile, "availability", None))]
        if any(values):
            section("Preferencias laborales"); story.append(paragraph(" · ".join(filter(None, values))))
    output = BytesIO()

    def page_details(canvas, doc):
        canvas.saveState()
        if layout == "modern":
            canvas.setFillColor(accent); canvas.rect(24, 40, 4, 762, fill=1, stroke=0)
        canvas.setStrokeColor(line); canvas.line(48, 35, 547, 35)
        canvas.setFont("Resume", 7); canvas.setFillColor(muted)
        canvas.drawString(48, 23, "Hoja de vida"); canvas.drawRightString(547, 23, f"Página {doc.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(output, pagesize=(595, 842), leftMargin=48, rightMargin=48, topMargin=40, bottomMargin=49,
                                 title=f"Hoja de vida - {user.name}", author=user.name, pageCompression=1)
    document.build(story, onFirstPage=page_details, onLaterPages=page_details)
    return output.getvalue()
