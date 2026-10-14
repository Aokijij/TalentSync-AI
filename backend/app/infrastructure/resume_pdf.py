"""Private, designed CVs. Preview and download use the same PDF bytes."""
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from PIL import Image as PillowImage
from PIL import ImageDraw, ImageOps
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas
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


def portrait(photo, size=76, circular=False):
    try:
        with PillowImage.open(BytesIO(photo)) as original:
            if original.width * original.height > 20_000_000:
                raise ValueError("Photo too large to decode")
            image = ImageOps.fit(ImageOps.exif_transpose(original).convert("RGB"), (400, 400)).convert("RGBA")
            mask = PillowImage.new("L", (400, 400), 0)
            drawing = ImageDraw.Draw(mask)
            if circular:
                drawing.ellipse((0, 0, 399, 399), fill=255)
            else:
                drawing.rounded_rectangle((0, 0, 399, 399), radius=32, fill=255)
            image.putalpha(mask)
            image_data = BytesIO(); image.save(image_data, format="PNG")
        image_data.seek(0)
        return Image(image_data, width=size, height=size)
    except (OSError, ValueError, PillowImage.DecompressionBombError):
        raise UseCaseError(status_code=422, detail="No pudimos incluir la foto. Reemplázala o desactiva Foto para exportar") from None


def classic_pdf(user, included, include_photo, photo, accent):
    profile = user.profile
    main = resume_pdf(user, sections=included & {"summary", "experiences", "educations", "evidence"}, include_photo=False, _layout="classic-main")
    light = colors.HexColor("#e2e8f0")
    style = ParagraphStyle("Side", fontName="Resume", fontSize=8.2, leading=12.5, textColor=light, spaceAfter=8)
    title = ParagraphStyle("SideTitle", parent=style, fontName="ResumeBold", fontSize=9, leading=14, textColor=colors.white, spaceBefore=20, spaceAfter=9, keepWithNext=True)
    def p(value, format=style):
        return Paragraph(escape(str(value or "")).replace("\n", "<br/>"), format)
    story = []
    if include_photo and photo:
        image = portrait(photo, 102)
        image.hAlign = "LEFT"
        story.extend([image, Spacer(1, 12)])
    if "contact" in included:
        story.append(p("CONTACTO", title))
        for value in [user.email, profile.phone, ", ".join(filter(None, [profile.location, profile.department]))]:
            if value:
                story.append(p(value))
    if "skills" in included and profile.skills:
        story.extend([p("HABILIDADES", title), p(" · ".join(profile.skills))])
    if "languages" in included and profile.languages:
        story.append(p("IDIOMAS", title))
        for item in profile.languages:
            story.append(p(f"{item.get('name', '')} · {'Nativo' if item.get('level') == 'NATIVE' else item.get('level', '')}"))
    if "certifications" in included and profile.certifications:
        story.append(p("CURSOS Y CERTIFICACIONES", title))
        for item in profile.certifications:
            story.append(p(item.get("name"), ParagraphStyle("SideCourse", parent=style, fontName="ResumeBold", spaceAfter=3)))
            story.append(p(" · ".join(str(item.get(key)) for key in ["issuer", "year"] if item.get(key))))
    if "preferences" in included:
        labels = {"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial", "immediate": "Disponibilidad inmediata", "two_weeks": "Disponible en 15 días", "one_month": "Disponible en 30 días", "negotiable": "Fecha acordada"}
        values = [profile.preferred_sector, labels.get(profile.preferred_modality), labels.get(profile.availability)]
        if any(values):
            story.append(p("PREFERENCIAS", title))
            story.extend(p(value) for value in values if value)
    side = BytesIO()
    document = SimpleDocTemplate(side, pagesize=(595, 842), leftMargin=36, rightMargin=437, topMargin=40, bottomMargin=50)
    def background(canvas, doc):
        canvas.setFillColor(accent); canvas.rect(0, 0, 178, 842, fill=1, stroke=0)
    document.build(story or [Spacer(1, 1)], onFirstPage=background, onLaterPages=background)
    main_pages, side_pages = PdfReader(BytesIO(main)).pages, PdfReader(BytesIO(side.getvalue())).pages
    writer = PdfWriter()
    for index in range(max(len(main_pages), len(side_pages))):
        if index < len(main_pages):
            page = writer.add_page(main_pages[index])
        else:
            page = writer.add_blank_page(width=595, height=842)
            overlay = BytesIO(); canvas = pdfcanvas.Canvas(overlay, pagesize=(595, 842))
            canvas.setFillColor(accent); canvas.rect(0, 0, 178, 842, fill=1, stroke=0)
            canvas.setFillColor(colors.HexColor("#526477")); canvas.setFont("Resume", 7)
            canvas.drawRightString(553, 23, f"Página {index + 1}"); canvas.save()
            page.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
        if index < len(side_pages):
            page.merge_page(side_pages[index])
    writer.add_metadata({"/Title": f"Hoja de vida - {user.name}", "/Author": user.name})
    output = BytesIO(); writer.write(output)
    return output.getvalue()


def resume_pdf(user, *, sections=None, include_photo=True, photo=None, _layout=None):
    fonts()
    profile = user.profile
    included = SECTIONS if sections is None else set(sections) & SECTIONS
    layout = _layout or profile.resume_style or "classic"
    accent = colors.HexColor(PALETTES.get(profile.resume_color, {"classic": "#0c4a6e", "modern": "#4338ca", "minimal": "#0f172a"}.get(layout, "#0c4a6e")))
    if layout == "classic":
        return classic_pdf(user, included, include_photo, photo, accent)
    column = layout == "classic-main"
    width = 343 if column else 499
    ink, muted, line = [colors.HexColor(value) for value in ("#172a3a", "#526477", "#dce4eb")]
    body_font, bold_font = ("Times-Roman", "Times-Bold") if layout == "minimal" else ("Resume", "ResumeBold")
    base = ParagraphStyle("CVBody", parent=getSampleStyleSheet()["Normal"], fontName=body_font, fontSize=10 if layout == "minimal" else 9, leading=14, textColor=ink, spaceAfter=7, splitLongWords=True)
    heading = ParagraphStyle("CVHeading", parent=base, fontName=bold_font, fontSize=13 if layout == "minimal" else 10.5, leading=16, textColor=ink if layout == "minimal" else accent, spaceBefore=16 if column else 12, spaceAfter=6, keepWithNext=True)
    role = ParagraphStyle("CVRole", parent=base, fontName=bold_font, fontSize=11 if layout == "minimal" else 9.5, leading=15, spaceBefore=9, spaceAfter=3, keepWithNext=True)
    meta = ParagraphStyle("CVMeta", parent=base, fontSize=8, leading=12, textColor=muted, spaceAfter=6)
    inverse = layout == "modern"
    name_style = ParagraphStyle("CVName", parent=base, fontName=bold_font, fontSize=27 if layout == "minimal" else 23, leading=31, textColor=colors.white if inverse else ink, spaceAfter=10)
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
    photo_flowable = portrait(photo, 84 if inverse else 64, circular=True) if include_photo and photo else None
    header = Table([[identity, photo_flowable]] if photo_flowable else [[identity]], colWidths=[width - 112, 112] if photo_flowable else [width])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 22 if inverse else 0), ("RIGHTPADDING", (0, 0), (-1, -1), 22 if inverse else 0),
        ("TOPPADDING", (0, 0), (-1, -1), 18 if inverse else 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 18 if inverse else 18),
        ("BACKGROUND", (0, 0), (-1, -1), accent if inverse else colors.HexColor("#f1f5f9") if layout == "modern" else colors.white),
        ("LINEBELOW", (0, 0), (-1, -1), 2 if layout != "minimal" else .7, accent),
    ]))
    story = [header, Spacer(1, 10)]
    if profile.profession and len(profile.profession) > 250:
        story.append(paragraph(profile.profession))
    if "contact" in included and len(contact_text) > 450:
        story.append(paragraph(contact_text, meta))

    def section(title):
        rule = HRFlowable(width="100%", thickness=.5, color=line, spaceAfter=7)
        rule.keepWithNext = True
        if layout == "modern":
            gap = Spacer(1, 6); gap.keepWithNext = True
            story.extend([paragraph(title.upper(), ParagraphStyle("ModernHeading", parent=heading, backColor=colors.HexColor("#f1f5f9"), borderPadding=7)), gap])
        else:
            story.extend([paragraph(title if layout == "minimal" else title.upper(), heading), rule])

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
        if column:
            canvas.setFillColor(accent); canvas.rect(0, 0, 178, 842, fill=1, stroke=0)
        canvas.setStrokeColor(line); canvas.line(212 if column else 48, 35, 553 if column else 547, 35)
        canvas.setFont("Resume", 7); canvas.setFillColor(muted)
        canvas.drawString(212 if column else 48, 23, "Hoja de vida"); canvas.drawRightString(553 if column else 547, 23, f"Página {doc.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(output, pagesize=(595, 842), leftMargin=212 if column else 48, rightMargin=40 if column else 48, topMargin=40, bottomMargin=49,
                                 title=f"Hoja de vida - {user.name}", author=user.name, pageCompression=1)
    document.build(story, onFirstPage=page_details, onLaterPages=page_details)
    return output.getvalue()
