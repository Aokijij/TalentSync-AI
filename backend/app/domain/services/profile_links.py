"""Optional professional references; never fetch user-supplied URLs."""
from urllib.parse import urlsplit

LINK_PLATFORMS = {
    "linkedin": ("LinkedIn", "linkedin.com"),
    "github": ("GitHub", "github.com"),
    "portfolio": ("Portafolio personal", None),
    "gitlab": ("GitLab", "gitlab.com"),
    "behance": ("Behance", "behance.net"),
    "dribbble": ("Dribbble", "dribbble.com"),
    "kaggle": ("Kaggle", "kaggle.com"),
    "stackoverflow": ("Stack Overflow", "stackoverflow.com"),
    "medium": ("Medium", "medium.com"),
    "youtube": ("YouTube", "youtube.com"),
    "other": ("Otro enlace", None),
}


def link_label(item):
    return item.get("label") or LINK_PLATFORMS.get(item.get("platform"), ("Enlace profesional", None))[0]


def professional_link_url(value):
    value = str(value or "").strip()
    parsed = urlsplit(value)
    _ = parsed.port
    if not value or len(value) > 500 or parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError("Usa un enlace HTTP o HTTPS de hasta 500 caracteres y sin credenciales")
    return value
