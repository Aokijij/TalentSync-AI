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
PILL_FONT, PILL_SIZE = "ResumeBold", 6.8


class Monogram(Flowable):
    def __init__(self, name, color, circular, size, gradient=None, frame=None, shadow=False):
        super().__init__(); self.width = self.height = size
        self.name, self.color, self.circular = name, color, circular
        self.gradient = gradient
        self.frame, self.shadow = frame, shadow

    def draw(self):
        c, size = self.canv, self.width
        if self.shadow:
            c.saveState(); c.setFillColor(colors.black); c.setFillAlpha(.025)
            for extra in (8, 5, 2):
                c.circle(size / 2, size / 2 - 4, size / 2 + extra, fill=1, stroke=0)
            c.restoreState()
        c.setFillColor(self.color)
        if self.circular:
            c.circle(size / 2, size / 2, size / 2, fill=1, stroke=0)
        else:
            c.roundRect(0, 0, size, size, 7, fill=1, stroke=0)
        if self.gradient:
            c.saveState()
            path = c.beginPath()
            if self.circular:
                path.circle(size / 2, size / 2, size / 2)
            else:
                path.roundRect(0, 0, size, size, 7)
            c.clipPath(path, stroke=0, fill=0)
            c.linearGradient(0, size, size, 0, self.gradient)
            c.restoreState()
        if self.frame:
            c.setStrokeColor(self.frame); c.setLineWidth(2)
            if self.circular:
                c.circle(size / 2, size / 2, size / 2 - 1, fill=0, stroke=1)
            else:
                c.roundRect(1, 1, size - 2, size - 2, 6, fill=0, stroke=1)
        initials = "".join(word[0] for word in str(self.name or "Candidato").split()[:2]).upper()
        c.setFillColor(colors.white); c.setFont("ResumeBold", 19)
        c.drawCentredString(size / 2, size / 2 - 7, initials)


class Timeline(Paragraph):
    def draw(self):
        c = self.canv
        c.saveState(); c.setStrokeColor(self.style.timelineLine); c.setLineWidth(.8)
        c.line(-8, -4, -8, self.height - 5)
        if self.style.timelineDot:
            c.setFillColor(colors.white); c.circle(-8, self.height - 6, 4, fill=1, stroke=1)
            c.setFillColor(self.style.timelineColor); c.circle(-8, self.height - 6, 2.4, fill=1, stroke=0)
        c.restoreState(); super().draw()


def gradient_panel(canvas, x, y, width, height, start, end):
    canvas.saveState()
    path = canvas.beginPath(); path.rect(x, y, width, height)
    canvas.clipPath(path, stroke=0, fill=0)
    canvas.linearGradient(x, y + height, x + width, y, [start, end])
    canvas.restoreState()


class ContactLine(Flowable):
    def __init__(self, value, style, kind):
        super().__init__()
        self.paragraph, self.style, self.kind = Paragraph(escape(str(value)), style), style, kind
        self.spaceAfter = style.spaceAfter

    def wrap(self, width, height):
        _, self.height = self.paragraph.wrap(max(20, width - 13), height)
        self.width = width
        return width, self.height

    def draw(self):
        c, y = self.canv, self.height - 7
        c.saveState(); c.setStrokeColor(self.style.textColor); c.setLineWidth(.6)
        if self.kind == "email":
            c.rect(0, y, 8, 6, fill=0, stroke=1); c.lines([(0, y + 6, 4, y + 2.5), (4, y + 2.5, 8, y + 6)])
        elif self.kind == "location":
            c.circle(4, y + 4, 3, fill=0, stroke=1); c.circle(4, y + 4, 1, fill=0, stroke=1)
            c.lines([(1.5, y + 2, 4, y - 2), (4, y - 2, 6.5, y + 2)])
        else:
            path = c.beginPath(); path.moveTo(1, y + 6); path.curveTo(-1, y + 1, 6, y - 3, 8, y)
            path.lineTo(6, y + 2); path.lineTo(4.5, y + 1); path.lineTo(2, y + 3.5); path.lineTo(3, y + 5); path.close()
            c.drawPath(path, stroke=1, fill=0)
        c.restoreState(); self.paragraph.drawOn(c, 13, 0)


class SkillPills(Flowable):
    def __init__(self, labels, foreground, background, border, transparent=False, square=False):
        super().__init__(); self.labels = labels
        self.foreground, self.background, self.border = foreground, background, border
        self.transparent, self.square = transparent, square
        self.height = 24

    def draw(self):
        c, x = self.canv, 0
        for label in self.labels:
            width = pdfmetrics.stringWidth(label, PILL_FONT, PILL_SIZE) + 14
            c.saveState()
            c.setFillColor(colors.white if self.transparent else self.background); c.setStrokeColor(colors.white if self.transparent else self.border); c.setLineWidth(.5)
            if self.transparent:
                c.setFillAlpha(.1); c.setStrokeAlpha(.2)
            c.roundRect(x, 4, width, 18, 3 if self.square else 9, fill=1, stroke=1)
            c.restoreState()
            c.setFillColor(self.foreground); c.setFont(PILL_FONT, PILL_SIZE); c.drawString(x + 7, 10, label)
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
    single_column = minimal
    body = ParagraphStyle("Body", fontName="Resume", fontSize=8.3, leading=13, textColor=ink, spaceAfter=8, splitLongWords=True)
    side_body = ParagraphStyle("Sidebar", parent=body, fontSize=7.6, leading=11.5, textColor=colors.white if modern else ink)
    meta = ParagraphStyle("Meta", parent=body, fontSize=7, leading=10, textColor=muted, spaceAfter=6)
    role = ParagraphStyle("Role", parent=body, fontName="ResumeBold", fontSize=9, leading=13, spaceAfter=3, keepWithNext=True, timelineColor=accent, timelineLine=line, timelineDot=True)
    company = ParagraphStyle("Company", parent=body, fontSize=8, textColor=accent, spaceAfter=4, keepWithNext=True, timelineColor=accent, timelineLine=line, timelineDot=False)
    timeline_body = ParagraphStyle("TimelineBody", parent=body, timelineColor=accent, timelineLine=line, timelineDot=False)

    def p(value, style=body, timeline=False):
        return (Timeline if timeline else Paragraph)(escape(str(value or "")).replace("\n", "<br/>"), style)

    header_color = colors.white if classic else ink
    eyebrow = ParagraphStyle("Eyebrow", parent=meta, fontName="ResumeBold", textColor=colors.HexColor("#cbd5e1") if classic else muted, fontSize=6, spaceAfter=6)
    name_style = ParagraphStyle("Name", parent=body, fontName="Times-Roman" if minimal else "ResumeBold", fontSize=25 if minimal else 24, leading=29, textColor=header_color, spaceAfter=7)
    identity = [p("H O J A  D E  V I D A", eyebrow), p(user.name, name_style)]
    long_profession = len(profile.profession or "") > 250
    if profile.profession and not long_profession:
        identity.append(p(profile.profession, ParagraphStyle("Profession", parent=body, fontSize=10, leading=14, textColor=colors.HexColor("#d5e2ef") if classic else ink if minimal else accent, spaceAfter=0)))
    contacts = [str(value) for value in [user.email, getattr(profile, "phone", None), ", ".join(filter(None, [profile.location, profile.department]))] if value] if "contact" in included else []
    long_contact = len(" ".join(contacts)) > 450
    contact_style = ParagraphStyle("Contact", parent=meta, textColor=header_color, fontSize=6.9, leading=11, spaceAfter=7)
    contact = [ContactLine(value, contact_style, kind) for value, kind in [(user.email, "email"), (getattr(profile, "phone", None), "phone"), (", ".join(filter(None, [profile.location, profile.department])), "location")] if value] if "contact" in included and not long_contact else []
    size = 62 if minimal else 80
    avatar_frame = colors.Color(*[value * .7 + .3 for value in (dark.red, dark.green, dark.blue)]) if classic else line
    avatar = portrait(photo, size, circular=not classic) if photo and include_photo else Monogram(user.name, accent, not classic, size, gradient=[accent, dark] if not minimal else None, frame=avatar_frame, shadow=modern) if include_photo else None
    cells, widths = ([avatar, identity, contact], [size + 18, 369 - size, 132]) if avatar else ([identity, contact], [387, 132])
    # Preserve the reference's right-hand contact column for ordinary names;
    # long names can use its width rather than spilling outside the header.
    if p(user.name, name_style).wrap(widths[-2] - 14, 500)[1] > 60:
        if contact:
            identity.append(Spacer(1, 8))
            identity.append(p(" · ".join(contacts), ParagraphStyle("WideContact", parent=contact_style, fontSize=7.2, leading=12, spaceAfter=0)))
        header = Table([[avatar, identity]] if avatar else [[identity]], colWidths=[104, 415] if avatar else [519])
    else:
        header = Table([cells], colWidths=widths)
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 14), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    header.setStyle(TableStyle([("RIGHTPADDING", (-1, 0), (-1, -1), 0)]))
    _, header_height = header.wrap(495, 500)
    header_height = max(132 if minimal else 160, header_height + 52)
    body_top = 842 - header_height

    def section(story, title, side=False):
        text_color = colors.white if modern and side else accent
        heading = ParagraphStyle("Section", parent=side_body if side else body, fontName="ResumeBold", fontSize=7.6 if side else 8.5, leading=13, textColor=text_color, spaceBefore=14, spaceAfter=7, keepWithNext=True)
        rule = HRFlowable(width="100%", thickness=.8, color=side_line if modern and side else accent if classic else line, hAlign="LEFT", spaceAfter=11)
        rule.keepWithNext = True
        story.extend([p(title.upper(), heading), rule])

    main, side = [], []
    if long_profession:
        main.append(p(profile.profession))
    if long_contact:
        main.extend(p(value, meta) for value in contacts)
    if "summary" in included and profile.experience:
        section(main, "Perfil profesional"); main.append(p(profile.experience))
    for title, key, primary, secondary in [("Experiencia", "experiences", "role", "company"), ("Formación", "educations", "degree", "institution"), ("Proyectos y logros", "evidence", "title", "")]:
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
            if minimal and key == "educations":
                title_row = Table([[p(item.get(primary), role), p(date, ParagraphStyle("CardDate", parent=meta, alignment=2))]], colWidths=[main_width - 124, 104])
                title_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                content = [title_row]
                if item.get(secondary):
                    content.append(p(item[secondary], company))
                if item.get("description"):
                    content.append(p(item["description"]))
                card = Table([[content]], colWidths=[main_width], splitInRow=1, cornerRadii=[7, 7, 7, 7])
                card.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), tint), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
                main.extend([card, Spacer(1, 12)])
                continue
            if date and len(str(item.get(primary) or "")) < 120:
                row = Table([[p(item.get(primary), role, timeline=True), p(date, ParagraphStyle("DateInline", parent=meta, alignment=2))]], colWidths=[main_width - 104, 104])
                row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                row.keepWithNext = True; main.append(row)
            else:
                main.append(p(item.get(primary), role, timeline=True))
                if date:
                    main.append(p(date, meta))
            if secondary and item.get(secondary):
                label = EDUCATION_LEVEL_LABELS.get(item.get("level")) if key == "educations" else None
                main.append(p(" · ".join(filter(None, [item[secondary], label])), company, timeline=True))
            if item.get("description"):
                main.append(p(item["description"], timeline_body, timeline=True))
            main.append(Spacer(1, 12))
    if "educations" in included and not getattr(profile, "educations", None) and profile.education:
        section(main, "Formación"); main.append(p(profile.education))
    long_skills = single_column
    target = main if single_column else side
    if "contact" in included and getattr(profile, "links", None):
        section(target, "Enlaces profesionales", not single_column)
        link_style = ParagraphStyle("ProfessionalLink", parent=meta if single_column else side_body, fontSize=7 if single_column else 6.8, leading=11 if modern else 10, spaceAfter=10 if modern else 9)
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
        skills = [f"{skill} · {SKILL_LEVEL_LABELS[levels[skill_key(skill)]]}" if skill_key(skill) in levels else skill for skill in profile.skills]
        # Each pill remains a splittable paragraph, so long skill lists never clip.
        pill = ParagraphStyle("Pill", parent=side_body if not single_column else body, fontName=PILL_FONT, fontSize=PILL_SIZE, leading=11, backColor=colors.white if classic else soft_accent if not minimal else tint,
                              textColor=accent if classic else colors.white if not minimal else ink, borderColor=line if classic else side_line if not minimal else line,
                              borderWidth=.5, borderPadding=5, borderRadius=3 if minimal else 9, spaceAfter=11)
        width, row, used = (519 if long_skills else 155 if minimal else 124), [], 0
        def flush():
            if row:
                target.append(SkillPills(list(row), pill.textColor, pill.backColor, pill.borderColor, transparent=modern, square=minimal))
                row.clear()
        for skill in skills:
            length = pdfmetrics.stringWidth(str(skill), PILL_FONT, PILL_SIZE) + 14
            if length > width:
                flush(); used = 0; target.append(p(skill, pill)); continue
            if used + length > width:
                flush(); used = 0
            row.append(str(skill)); used += length + 5
        flush()
    ancillary_sections = []
    if "languages" in included and profile.languages:
        if not single_column:
            ancillary_sections.append((len(side), "Idiomas"))
        section(target, "Idiomas", not single_column)
        language_style = ParagraphStyle("ModernLanguage", parent=side_body, leading=12, spaceAfter=9) if modern else body
        target.extend(p(f"{item.get('name', item.get('language', ''))} · {'Nativo' if item.get('level') == 'NATIVE' else item.get('level', '')}", language_style) for item in profile.languages)
    if "certifications" in included and profile.certifications:
        if not single_column:
            ancillary_sections.append((len(side), "Cursos y certificaciones"))
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
    if "certifications" in included:
        from app.domain.services.credentials import profile_credentials, validity
        documents = [("Licencia de conducción", row, True) for row in profile_credentials(profile, "driving_licenses")] + [("Tarjeta profesional", row, False) for row in profile_credentials(profile, "professional_cards")]
        if documents:
            if not single_column:
                ancillary_sections.append((len(side), "Licencias y tarjetas"))
            section(target, "Licencias y tarjetas", not single_column)
            for label, row, driving in documents:
                target.append(p(f"{label}: {row.get('category') if driving else row.get('profession')}", side_body if not single_column else body))
                status = {"declared": "Vigencia declarada", "review": "Por confirmar", "not_met": "Vencida, suspendida o en trámite"}[validity(row, driving=driving)]
                content = [status, row.get("issuer"), f"N.º {row['number']}" if row.get("number") else None, f"Vence {row['expires_on']}" if row.get("expires_on") else None]
                target.append(p(" · ".join(str(item) for item in content if item), side_body if not single_column else meta))
    if "preferences" in included:
        values = [profile.preferred_sector, LABELS.get(profile.preferred_modality), LABELS.get(profile.availability)]
        if any(values):
            if not single_column:
                ancillary_sections.append((len(side), "Preferencias"))
            section(target, "Preferencias", not single_column)
            present = [value for value in values if value]
            if modern:
                target.append(p(" · ".join(present), side_body))
            else:
                for index, value in enumerate(present):
                    target.append(p(value, ParagraphStyle("Preference", parent=body, keepWithNext=index < len(present) - 1)))
    def draw_header(c):
        c.setFillColor(dark if classic else colors.white); c.rect(0, body_top, 595, header_height - 16, stroke=0, fill=1)
        if modern:
            gradient_panel(c, 0, 820, 595, 6, dark, accent)
        elif not classic:
            c.setFillColor(accent); c.rect(0, 823, 595, 3, stroke=0, fill=1)
        header.drawOn(c, 38, body_top + (header_height - 16 - header.wrap(519, 500)[1]) / 2)
        c.setStrokeColor(line); c.setLineWidth(.5); c.line(0, body_top, 595, body_top)

    def paginate(story, x, width):
        output = BytesIO()
        doc = BaseDocTemplate(output, pagesize=(595, 842), leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0, pageCompression=1)
        frame = lambda top: Frame(x, 42, width, top - 42, leftPadding=8, rightPadding=8, topPadding=9, bottomPadding=8)
        doc.addPageTemplates([PageTemplate(id="First", frames=[frame(body_top)], autoNextPageTemplate="Next"), PageTemplate(id="Next", frames=[frame(807)])])
        doc.build(list(story) or [Spacer(1, 1)])
        return PdfReader(BytesIO(output.getvalue())).pages

    main_pages = paginate(main, 30 if single_column else 186, 535 if single_column else 379)
    side_pages = [] if single_column else paginate(side, 24, 140)
    if not single_column and len(side_pages) > len(main_pages):
        # Keep optional details together and use free space in the main column
        # before adding a page solely for the end of a full sidebar.
        for index in reversed(range(len(ancillary_sections))):
            start = ancillary_sections[index][0]
            shorter_side = paginate(side[:start], 24, 140)
            if len(shorter_side) >= len(side_pages):
                continue
            balanced_main = list(main)
            for offset in range(index, len(ancillary_sections)):
                group_start, title = ancillary_sections[offset]
                group_end = ancillary_sections[offset + 1][0] if offset + 1 < len(ancillary_sections) else len(side)
                section(balanced_main, title)
                # Each section starts with a heading and rule. Recreate its
                # text with main-column colours, retaining emphasis and links.
                for item in side[group_start + 2:group_end]:
                    if isinstance(item, Paragraph):
                        style = ParagraphStyle("BalancedDetail", parent=body, fontName=item.style.fontName, spaceAfter=item.style.spaceAfter)
                        balanced_main.append(Paragraph(item.text, style))
                    else:
                        balanced_main.append(item)
            balanced_pages = paginate(balanced_main, 186, 379)
            if max(len(balanced_pages), len(shorter_side)) < len(side_pages):
                main_pages, side_pages = balanced_pages, shorter_side
                break
    count = max(len(main_pages), len(side_pages))
    writer = PdfWriter()
    for index in range(count):
        background = BytesIO(); c = Canvas(background, pagesize=(595, 842))
        c.setFillColor(colors.white); c.rect(0, 0, 595, 842, stroke=0, fill=1)
        if not single_column:
            if classic:
                c.setFillColor(tint); c.rect(0, 0, 178, body_top if index == 0 else 842, stroke=0, fill=1)
            else:
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
