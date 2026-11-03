"""Stable identities for learning records imported through different flows."""
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


def training_text(value):
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return re.sub(r"[^a-z0-9]+", " ", "".join(c for c in text if not unicodedata.combining(c))).strip()


def training_keys(row):
    name = training_text(row.get("name") or row.get("title"))
    issuer = training_text(row.get("issuer") or row.get("provider"))
    keys = set()
    if row.get("resource_id"):
        keys.add(("resource", str(row["resource_id"])))
    url = str(row.get("url") or row.get("credential_url") or "").strip()
    if url:
        parsed = urlsplit(url)
        keys.add(("url", urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), parsed.query, ""))))
    if name and issuer:
        keys.add(("title", name, issuer, str(row.get("year") or "")))
    if row.get("certificate_id") and issuer:
        keys.add(("credential", issuer, str(row["certificate_id"]).casefold()))
    return keys


def unique_training(rows):
    result, identities = [], []
    for source in rows or []:
        row = dict(source)
        keys = training_keys(row)
        found = next((index for index, previous in enumerate(identities) if keys & previous), None)
        if found is None:
            result.append(row)
            identities.append(keys)
            continue
        previous = result[found]
        result[found] = {**previous, **{key: value for key, value in row.items() if value not in (None, "", [], {})}}
        # Keep the first stable identifier so existing evidence links keep working.
        if previous.get("id"):
            result[found]["id"] = previous["id"]
        if previous.get("skills") or row.get("skills"):
            result[found]["skills"] = list(dict.fromkeys([*previous.get("skills", []), *row.get("skills", [])]))
        identities[found] |= keys
    return result
