import re
import unicodedata
from urllib.parse import quote


def resume_filename(name):
    safe = re.sub(r'[\x00-\x1f\\/:*?"<>|]', " ", str(name or "Candidato"))
    safe = re.sub(r"\s+", " ", safe).strip().rstrip(". ")[:120] or "Candidato"
    return f"{safe} - TalentSync - Hoja de vida.pdf"


def resume_disposition(name, inline=False):
    filename = resume_filename(name)
    fallback = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode()
    return f"{'inline' if inline else 'attachment'}; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename)}"
