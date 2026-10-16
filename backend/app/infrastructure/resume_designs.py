"""Original CV layouts, with independently paginated columns and one PDF preview."""
from io import BytesIO
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.domain.services.credential_links import certificate_url
from app.domain.services.experience_dates import recent_experiences
from app.domain.services.professions import EDUCATION_LEVEL_LABELS
from app.domain.services.profile_links import link_label, professional_link_url
from app.domain.services.resume_filename import resume_filename
from app.domain.services.skill_levels import SKILL_LEVEL_LABELS, declared_skill_levels
from app.domain.services.skills import skill_key
from app.infrastructure.resume_pdf import date_label, portrait

PALETTES = {
    "default": ("#0c4a6e", "#020617", "#eef6fc", "#bfdbfe"),
    "forest": ("#166534", "#12382b", "#f0fdf4", "#bbf7d0"),
    "wine": ("#881337", "#4c1025", "#fff1f2", "#fecdd3"),
    "slate": ("#334155", "#1e293b", "#f8fafc", "#cbd5e1"),
    "navy": ("#1e3a8a", "#172554", "#eff6ff", "#bfdbfe"),
    "blue": ("#1d4ed8", "#172554", "#eff6ff", "#bfdbfe"),
    "teal": ("#0f766e", "#134e4a", "#f0fdfa", "#99f6e4"),
    "rose": ("#be185d", "#500724", "#fdf2f8", "#fbcfe8"),
}
LABELS = {"remote": "Remoto", "hybrid": "Híbrido", "onsite": "Presencial", "immediate": "Inmediata", "two_weeks": "En 15 días", "one_month": "En 30 días", "negotiable": "Fecha acordada"}


class Monogram(Flowable):
    def __init__(self, name, color, circular, size, gradient=None):
        super().__init__(); self.width = self.height = size
        self.name, self.color, self.circular = name, color, circular
        self.gradient = gradient

    def draw(self):
        c, size = self.canv, self.width
        c.setFillColor(self.color)
        if self.circular:
            c.circle(size / 2, size / 2, size / 2, fill=1, stroke=0)
            if self.gradient:
                c.saveState()
                path = c.beginPath(); path.circle(size / 2, size / 2, size / 2)
                c.clipPath(path, stroke=0, fill=0)
                c.linearGradient(0, size, size, 0, self.gradient)
                c.restoreState()
        else:
            c.roundRect(0, 0, size, size, 7, fill=1, stroke=0)
        initials = "".join(word[0] for word in str(self.name or "Candidato").split()[:2]).upper()
        c.setFillColor(colors.white); c.setFont("ResumeBold", 19)
        c.drawCentredString(size / 2, size / 2 - 7, initials)


class Timeline(Paragraph):
    def draw(self):
        c = self.canv
        c.saveState(); c.setStrokeColor(self.style.timelineColor); c.setLineWidth(.6)
        c.line(-8, -4, -8, self.height - 5)
        if self.style.timelineDot:
            c.setFillColor(self.style.timelineColor); c.circle(-8, self.height - 6, 2.8, fill=1, stroke=0)
        c.restoreState(); super().draw()


def gradient_panel(canvas, x, y, width, height, start, end):
    canvas.saveState()
    path = canvas.beginPath(); path.rect(x, y, width, height)
    canvas.clipPath(path, stroke=0, fill=0)
    canvas.linearGradient(x, y + height, x + width, y, [start, end])
    canvas.restoreState()


class SkillPills(Flowable):
    def __init__(self, labels, foreground, background, border):
        super().__init__(); self.labels = labels
        self.foreground, self.background, self.border = foreground, background, border
        self.height = 26

    def draw(self):
        c, x = self.canv, 0
        for label in self.labels:
            width = pdfmetrics.stringWidth(label, "Resume", 7) + 14
            c.setFillColor(self.background); c.setStrokeColor(self.border); c.setLineWidth(.5)
            c.roundRect(x, 5, width, 19, 9, fill=1, stroke=1)
            c.setFillColor(self.foreground); c.setFont("Resume", 7); c.drawString(x + 7, 11, label)
            x += width + 5


def build_resume(user, included, include_photo, photo):
    profile = user.profile
    layout = profile.resume_style if profile.resume_style in {"classic", "modern", "minimal"} else "classic"
    palette = PALETTES.get(profile.resume_color, PALETTES["default"])
    if profile.resume_color == "default" and layout == "modern":
        palette = ("#4338ca", "#312e81", "#eef2ff", "#c7d2fe")
    elif profile.resume_color == "default" and layout == "minimal":
        palette = ("#0f172a", "#0f172a", "#f8fafc", "#cbd5e1")
    accent, dark, tint, line = map(colors.HexColor, palette)
    soft_accent = colors.Color(*[value * .8 + .2 for value in (dark.red, dark.green, dark.blue)])
    side_line = colors.Color(*[value * .65 + .35 for value in (dark.red, dark.green, dark.blue)])
    ink, muted = colors.HexColor("#172a3a"), colors.HexColor("#526477")
    minimal, classic, modern = layout == "minimal", layout == "classic", layout == "modern"
    single_column = minimal or classic
    body = ParagraphStyle("Body", fontName="Times-Roman" if classic else "Resume", fontSize=9.3 if classic else 8.3, leading=14 if classic else 13, textColor=ink, spaceAfter=6 if modern else 8, splitLongWords=True)
    side_body = ParagraphStyle("Sidebar", parent=body, fontSize=7.6, leading=11.5, textColor=colors.white if modern else ink)
    meta = ParagraphStyle("Meta", parent=body, fontSize=7, leading=10, textColor=muted, spaceAfter=6)
    role = ParagraphStyle("Role", parent=body, fontName="Times-Bold" if classic else "ResumeBold", fontSize=10 if classic else 9, leading=14 if classic else 13, spaceAfter=3, keepWithNext=True, timelineColor=accent, timelineDot=True)
    company = ParagraphStyle("Company", parent=body, fontSize=8, textColor=accent, spaceAfter=4, keepWithNext=True, timelineColor=line, timelineDot=False)
    timeline_body = ParagraphStyle("TimelineBody", parent=body, timelineColor=line, timelineDot=False)

    def p(value, style=body, timeline=False):
        return (Timeline if timeline else Paragraph)(escape(str(value or "")).replace("\n", "<br/>"), style)

    header_color = ink
    identity = [] if minimal else [p("H O J A  D E  V I D A", ParagraphStyle("Eyebrow", parent=meta, fontName="ResumeBold", textColor=accent if classic else muted, fontSize=6, spaceAfter=6, alignment=1 if classic else 0))]
    identity.append(p(user.name, ParagraphStyle("Name", parent=body, fontName="Times-Bold" if classic else "ResumeBold", fontSize=28 if classic else 25, leading=30 if modern else 32, textColor=header_color, spaceAfter=7, alignment=1 if classic else 0)))
    long_profession = len(profile.profession or "") > 250
    if profile.profession and not long_profession:
        identity.append(p(profile.profession, ParagraphStyle("Profession", parent=body, fontSize=10, leading=14, textColor=accent, spaceAfter=0, alignment=1 if classic else 0)))
    contacts = [str(value) for value in [user.email, getattr(profile, "phone", None), ", ".join(filter(None, [profile.location, profile.department]))] if value] if "contact" in included else []
    long_contact = len(" ".join(contacts)) > 450
    contact_style = ParagraphStyle("Contact", parent=meta, textColor=header_color, fontSize=6.9, leading=11, spaceAfter=7)
    contact = [p(value, contact_style) for value in contacts] if not long_contact else []
    size = 80 if modern else 54 if minimal else 65
    avatar = portrait(photo, size, circular=not classic) if photo and include_photo else Monogram(user.name, accent if classic or modern else dark, not classic, size, gradient=[accent, dark] if modern else None) if include_photo else None
    cells, widths = ([avatar, identity, contact], [size + 15, 335 - size, 145]) if avatar else ([identity, contact], [350, 145])
    if classic:
        centered_contact = p(" · ".join(contacts) if not long_contact else "", ParagraphStyle("CenteredContact", parent=contact_style, alignment=1, spaceBefore=12))
        header = Table([[identity, avatar or ""], [centered_contact, ""]], colWidths=[420, 75])
        header.setStyle(TableStyle([("SPAN", (0, 1), (1, 1))]))
        if not avatar:
            header.setStyle(TableStyle([("SPAN", (0, 0), (1, 0))]))
    elif modern:
        # Give the name the entire content width; contacts no longer compete
        # with it for a separate column, especially with long Spanish names.
        if contact:
            identity.append(Spacer(1, 8))
            identity.append(p(" · ".join(contacts), ParagraphStyle("ModernContact", parent=contact_style, fontSize=7.2, leading=12, textColor=muted, spaceAfter=0)))
        header = Table([[avatar, identity]] if avatar else [[identity]], colWidths=[104, 415] if avatar else [519])
    else:
        header = Table([cells], colWidths=widths)
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 14), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    _, header_height = header.wrap(495, 500)
    header_height = max(148 if modern else 112 if minimal else 135, header_height + (36 if modern else 45))
    body_top = 842 - header_height

    def section(story, title, side=False):
        text_color = colors.white if modern and side else accent if not modern else ink
        heading = ParagraphStyle("Section", parent=side_body if side else body, fontName="Times-Bold" if classic else "ResumeBold", fontSize=9.5 if classic else 7.6 if side else 8.5, leading=13, textColor=text_color, spaceBefore=8 if modern and side else 10 if modern else 17 if minimal else 13, spaceAfter=4 if modern and side else 10 if classic else 6, keepWithNext=True, backColor=tint if classic else None, borderPadding=6 if classic else 0)
        rule = HRFlowable(width=28 if modern and not side else "100%", thickness=2 if modern and not side else .6, color=side_line if modern and side else accent if modern else line, hAlign="LEFT", spaceAfter=7 if modern and side else 8 if modern else 10)
        rule.keepWithNext = True
        story.append(p(title if minimal else title.upper(), heading))
        if not single_column:
            story.append(rule)

    main, side = [], []
    if long_profession:
        main.append(p(profile.profession))
    if long_contact:
        main.extend(p(value, meta) for value in contacts)
    if "summary" in included and profile.experience:
        section(main, "Perfil profesional"); main.append(p(profile.experience))
    for title, key, primary, secondary in [("Experiencia", "experiences", "role", "company"), ("Formación académica", "educations", "degree", "institution"), ("Proyectos y logros", "evidence", "title", "")]:
        items = getattr(profile, key, None) or []
        if key not in included or not items:
            continue
        section(main, title)
        if key == "experiences":
            items = recent_experiences(items)
        for item in items:
            dates = [item.get("start_date") or item.get("start_year"), ("En curso" if key == "educations" else "Actualidad") if item.get("is_current") else item.get("end_date") or item.get("end_year") or item.get("year")]
            date = " - ".join(date_label(value) for value in dates if value)
            # Separate flowables allow arbitrarily long roles and descriptions to split.
            main_width = 519 if single_column else 363
            if date and len(str(item.get(primary) or "")) < 120:
                row = Table([[p(item.get(primary), role, timeline=not single_column), p(date, ParagraphStyle("DateInline", parent=meta, alignment=2))]], colWidths=[main_width - 104, 104])
                row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                row.keepWithNext = True; main.append(row)
            else:
                main.append(p(item.get(primary), role, timeline=not single_column))
                if date:
                    main.append(p(date, meta))
            if secondary and item.get(secondary):
                label = EDUCATION_LEVEL_LABELS.get(item.get("level")) if key == "educations" else None
                main.append(p(" · ".join(filter(None, [item[secondary], label])), company, timeline=not single_column))
            if item.get("description"):
                main.append(p(item["description"], timeline_body, timeline=not single_column))
            main.append(Spacer(1, 6 if modern else 8))
    if "educations" in included and not getattr(profile, "educations", None) and profile.education:
        section(main, "Formación académica"); main.append(p(profile.education))
    long_skills = single_column
    target = main if single_column else side
    if "contact" in included and getattr(profile, "links", None):
        section(target, "Enlaces profesionales", not single_column)
        link_style = ParagraphStyle("ProfessionalLink", parent=meta if single_column else side_body, fontSize=7 if single_column else 6.8, leading=10, spaceAfter=7 if modern else 9)
        for item in profile.links:
            try:
                url = professional_link_url(item.get("url"))
            except ValueError:
                url = ""
            if not url:
                continue
            caption = escape(link_label(item))
            display = escape(url.removeprefix("https://").removeprefix("http://").removeprefix("www.").rstrip("/"))
            target.append(Paragraph(f'<link href="{escape(url, {chr(34): "&quot;"})}"><b>{caption}</b><br/>{display}</link>', link_style))
    if "skills" in included and profile.skills:
        section(target, "Habilidades", not single_column)
        levels = declared_skill_levels(profile)
        skills = [f"{skill} ({SKILL_LEVEL_LABELS[levels[skill_key(skill)]]})" if skill_key(skill) in levels else skill for skill in profile.skills]
        # Each pill remains a splittable paragraph, so long skill lists never clip.
        pill = ParagraphStyle("Pill", parent=side_body if not single_column else body, fontSize=7.2, leading=11, backColor=colors.white if classic else soft_accent if not minimal else tint,
                              textColor=accent if classic else colors.white if not minimal else ink, borderColor=line if classic else side_line if not minimal else line,
                              borderWidth=.5, borderPadding=5, borderRadius=8, spaceAfter=10)
        width, row, used = (519 if long_skills else 155 if minimal else 124), [], 0
        def flush():
            if row:
                target.append(SkillPills(list(row), pill.textColor, pill.backColor, pill.borderColor))
                row.clear()
        for skill in ([] if minimal or not single_column else skills):
            length = pdfmetrics.stringWidth(str(skill), "Resume", 7) + 14
            if length > width:
                flush(); used = 0; target.append(p(skill, pill)); continue
            if used + length > width:
                flush(); used = 0
            row.append(str(skill)); used += length + 5
        flush()
        if not single_column:
            skill_style = ParagraphStyle("ModernSkill", parent=side_body, fontSize=7.6, leading=10.5, spaceAfter=5)
            for skill in profile.skills:
                level = SKILL_LEVEL_LABELS.get(levels.get(skill_key(skill)), "Nivel sin indicar")
                inline = pdfmetrics.stringWidth(str(skill), "ResumeBold", 7.6) + pdfmetrics.stringWidth(level, "Resume", 6.7) + 8 <= 124
                separator = " · " if inline else "<br/>"
                target.append(Paragraph(f'<b>{escape(str(skill))}</b>{separator}<font size="6.7" color="#e2e8f0">{escape(level)}</font>', skill_style))
        if minimal:
            target.append(p(" · ".join(skills)))
    if "languages" in included and profile.languages:
        section(target, "Idiomas", not single_column)
        target.extend(p(f"{item.get('name', item.get('language', ''))} · {'Nativo' if item.get('level') == 'NATIVE' else item.get('level', '')}", side_body if not single_column else body) for item in profile.languages)
    if "certifications" in included and profile.certifications:
        section(target, "Cursos y certificaciones", not single_column)
        for item in profile.certifications:
            target.append(p(item.get("name"), ParagraphStyle("Course", parent=side_body if not single_column else body, fontName="ResumeBold", keepWithNext=True)))
            target.append(p(" · ".join(str(item.get(key)) for key in ["issuer", "year"] if item.get(key)), side_body if not single_column else meta))
            try:
                url = certificate_url(item.get("url"))
            except ValueError:
                url = ""
            if url:
                target.append(Paragraph(f'<link href="{escape(url, {chr(34): "&quot;"})}">Ver certificado</link>', side_body if not single_column else meta))
    if "preferences" in included:
        values = [profile.preferred_sector, LABELS.get(profile.preferred_modality), LABELS.get(profile.availability)]
        if any(values):
            section(target, "Preferencias", not single_column)
            present = [value for value in values if value]
            if modern:
                target.append(p(" · ".join(present), side_body))
            else:
                for index, value in enumerate(present):
                    target.append(p(value, ParagraphStyle("Preference", parent=body, keepWithNext=index < len(present) - 1)))
    def draw_header(c):
        c.setFillColor(colors.white); c.rect(0, body_top, 595, header_height, stroke=0, fill=1)
        if classic:
            c.setStrokeColor(accent); c.setLineWidth(2); c.line(38, body_top + 10, 557, body_top + 10)
        if modern:
            gradient_panel(c, 0, 837, 595, 5, dark, accent)
        elif not classic:
            c.setFillColor(accent); c.rect(0, 837, 595, 5 if not minimal else 2, stroke=0, fill=1)
        header.drawOn(c, 38, body_top + (header_height - header.wrap(519 if modern else 495, 500)[1]) / 2)
        c.setStrokeColor(line); c.setLineWidth(.5); c.line(0, body_top, 595, body_top)

    def paginate(story, x, width):
        output = BytesIO()
        doc = BaseDocTemplate(output, pagesize=(595, 842), leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0, pageCompression=1)
        frame = lambda top: Frame(x, 42, width, top - 42, leftPadding=8, rightPadding=8, topPadding=9, bottomPadding=8)
        doc.addPageTemplates([PageTemplate(id="First", frames=[frame(body_top)], autoNextPageTemplate="Next"), PageTemplate(id="Next", frames=[frame(807)])])
        doc.build(story or [Spacer(1, 1)])
        return PdfReader(BytesIO(output.getvalue())).pages

    main_pages = paginate(main, 30 if single_column else 186, 535 if single_column else 379)
    side_pages = [] if single_column else paginate(side, 24, 140)
    count = max(len(main_pages), len(side_pages))
    writer = PdfWriter()
    for index in range(count):
        background = BytesIO(); c = Canvas(background, pagesize=(595, 842))
        c.setFillColor(colors.white); c.rect(0, 0, 595, 842, stroke=0, fill=1)
        if not single_column:
            gradient_panel(c, 0, 0, 178, body_top if index == 0 else 842, dark, accent)
        if index == 0:
            draw_header(c)
        else:
            c.setFont("Resume", 7); c.setFillColor(muted); c.drawRightString(557, 820, "Hoja de vida · Continuación")
        c.setFont("Resume", 6.5); c.setFillColor(muted); c.drawRightString(557, 22, f"Página {index + 1} de {count}")
        c.save(); page = writer.add_page(PdfReader(BytesIO(background.getvalue())).pages[0])
        if index < len(main_pages):
            page.merge_page(main_pages[index])
        if index < len(side_pages):
            page.merge_page(side_pages[index])
    writer.add_metadata({"/Title": resume_filename(user.name).removesuffix(".pdf"), "/Author": user.name})
    output = BytesIO(); writer.write(output)
    return output.getvalue()
