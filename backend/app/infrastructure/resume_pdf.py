"""Private, designed CVs. Preview and download use the same PDF bytes."""
import re
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import reportlab
from PIL import Image as PillowImage
from PIL import ImageDraw, ImageOps
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
)

from app.application.errors import UseCaseError

SECTIONS = {"contact", "summary", "experiences", "educations", "certifications", "driving_licenses", "professional_cards", "skills", "languages", "evidence", "preferences"}
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



def resume_pdf(user, *, sections=None, include_photo=True, photo=None):
    from app.infrastructure.resume_designs import build_resume
    fonts()
    return build_resume(user, SECTIONS if sections is None else set(sections) & SECTIONS, include_photo, photo)
