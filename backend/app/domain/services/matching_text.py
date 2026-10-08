import re


def professional_text(profile):
    """Use professional fields and remove known identifiers, without raw CV text.

    Free descriptions may still contain unidentified personal information; this
    is data minimization, not a guarantee of complete anonymization.
    """
    experiences = getattr(profile, "experiences", None) or []
    educations = getattr(profile, "educations", None) or []
    parts = [getattr(profile, "profession", None) or "", " ".join(profile.skills or []),
             " ".join(f"{row.get('role', '')} {row.get('description', '')}" for row in experiences),
             " ".join(row.get("degree", "") for row in educations),
             " ".join(row.get("name", "") for row in getattr(profile, "certifications", None) or [])]
    if not experiences:
        parts.append(getattr(profile, "experience", None) or "")
    text = " ".join(parts)
    user = getattr(profile, "user", None)
    excluded = [getattr(user, "name", None), getattr(user, "email", None), getattr(profile, "phone", None)]
    excluded += [row.get("company") for row in experiences] + [row.get("institution") for row in educations]
    for value in sorted((str(value) for value in excluded if value and len(str(value)) >= 3), key=len, reverse=True):
        text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
    return re.sub(r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b", " ", text)
