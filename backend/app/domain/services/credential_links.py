from urllib.parse import urlsplit


def certificate_url(value):
    """Validate a user-supplied link without fetching the remote document."""
    value = str(value or "").strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    _ = parsed.port
    if len(value) > 2000 or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError("El enlace del certificado debe ser una URL HTTPS válida sin credenciales")
    return value
