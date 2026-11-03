"""Confirmed source context remains tied to the exact accepted experience."""
from copy import deepcopy
from types import SimpleNamespace


def original_context_profile(profile):
    records = deepcopy(getattr(profile, "experiences", None) or [])
    changed = False
    entries = (getattr(profile, "preferences", None) or {}).get("writing_contexts", [])
    for entry in entries[:20]:
        index = entry.get("index")
        original = entry.get("record")
        if type(index) is not int or not isinstance(original, dict) or not 0 <= index < len(records):
            continue
        if records[index] == {**original, "description": entry.get("after")}:
            records[index] = original
            changed = True
    if not changed:
        return None
    baseline = SimpleNamespace(**{key: getattr(profile, key, None) for key in ("profession", "skills", "experience", "education", "educations", "certifications", "preferred_sector", "phone", "user", "preferences", "evidence")}, experiences=records)
    return baseline


def remember_writing_context(profile, proposal, applying):
    prefs = dict(profile.preferences or {})
    entries = prefs.get("writing_contexts", [])
    index = proposal["index"]
    original = proposal["record"]
    if applying:
        previous = next((item for item in entries if item.get("index") == index and original == {**item.get("record", {}), "description": item.get("after")}), None)
        if previous:
            original = previous["record"]
        entries = [item for item in entries if item.get("index") != index]
        entries = [{"index": index, "record": original, "after": proposal["after"]}, *entries][:20]
    else:
        entries = [item for item in entries if item.get("index") != index]
    profile.preferences = {**prefs, "writing_contexts": entries}
