"""Private, paginated CV download. No browser print dialog or remote service."""
from io import BytesIO
from textwrap import wrap

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def resume_pdf(user):
    profile = user.profile
    colors = {"forest": "0.086 0.396 0.204", "wine": "0.533 0.075 0.216", "slate": "0.2 0.255 0.333", "navy": "0.118 0.227 0.541", "blue": "0.114 0.306 0.847", "teal": "0.059 0.463 0.431", "rose": "0.745 0.094 0.365"}
    defaults = {"classic": "0.047 0.29 0.431", "modern": "0.263 0.22 0.792", "minimal": "0.059 0.09 0.165"}
    accent = colors.get(profile.resume_color, defaults.get(profile.resume_style, defaults["classic"]))
    writer = PdfWriter()
    regular = writer._add_object(DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica"), NameObject("/Encoding"): NameObject("/WinAnsiEncoding")}))
    bold = writer._add_object(DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica-Bold"), NameObject("/Encoding"): NameObject("/WinAnsiEncoding")}))
    layout = profile.resume_style or "classic"
    decorations = [f"{accent} RG 2 w 48 805 m 547 805 l S"] if layout == "minimal" else [f"{accent} rg 32 48 {5 if layout == 'modern' else 2} 754 re f"]
    commands, y = list(decorations), 790

    def flush():
        page = writer.add_blank_page(width=595, height=842)
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): regular, NameObject("/F2"): bold})})
        stream = DecodedStreamObject()
        stream.set_data("\n".join(commands).encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)

    def text(value, size=10, heading=False):
        nonlocal y, commands
        for paragraph in str(value or "").splitlines():
            for line in wrap(paragraph, width=88 if size <= 11 else 65 if size <= 15 else 36, break_long_words=True):
                if y < 55:
                    flush(); commands = list(decorations); y = 790
                encoded = line.encode("cp1252", errors="replace").hex()
                commands.append(f"BT /F{2 if heading else 1} {size} Tf {accent if heading else '0.12 0.16 0.22'} rg 1 0 0 1 48 {y} Tm <{encoded}> Tj ET")
                y -= size + 5
        y -= 7

    text(user.name, 20 if layout == "minimal" else 28 if layout == "modern" else 25, True)
    text(profile.profession, 14, True)
    text(" · ".join(str(value) for value in [user.email, profile.phone, profile.location] if value))
    if profile.experience:
        text("Perfil profesional", 14, True); text(profile.experience)
    for title, key, fields in [
        ("Experiencia laboral", "experiences", ["role", "company"]),
        ("Formación académica", "educations", ["degree", "institution"]),
        ("Cursos y certificaciones", "certifications", ["name", "issuer"]),
        ("Muestras de trabajo", "evidence", ["title"]),
    ]:
        items = getattr(profile, key, None) or []
        if items:
            text(title, 14, True)
            for item in items:
                text(" · ".join(str(item.get(field) or "") for field in fields if item.get(field)), 11, True)
                ongoing_label = "En curso" if key == "educations" else "Actualidad"
                text(" – ".join(str(value) for value in [item.get("start_date") or item.get("start_year"), ongoing_label if item.get("is_current") else item.get("end_date") or item.get("end_year")] if value))
                text(item.get("description") or "")
    if profile.skills:
        text("Habilidades", 14, True); text(" · ".join(profile.skills))
    if profile.languages:
        text("Idiomas", 14, True)
        text(" · ".join(f"{item.get('name', item.get('language', ''))}: {item.get('level', '')}" for item in profile.languages))
    flush()
    output = BytesIO(); writer.write(output)
    return output.getvalue()
