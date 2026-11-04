"""Identity terms used locally to minimize an explicitly requested AI draft."""


def private_writing_terms(user, profile):
    terms = [getattr(user, "name", ""), getattr(user, "email", ""), getattr(profile, "phone", "")]
    terms.extend(str(getattr(user, "name", "")).split())
    terms.extend(row.get("company", "") for row in getattr(profile, "experiences", None) or [])
    terms.extend(row.get("institution", "") for row in getattr(profile, "educations", None) or [])
    return [str(term).strip() for term in terms if term and len(str(term).strip()) >= 3]
