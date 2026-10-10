"""Conservative public enrollment information, independent from local plan progress."""
from datetime import date


def availability(resource, today=None):
    today = today or date.today()
    enrollment = (resource.get("details") or {}).get("enrollment") or {}
    observation = resource.get("source", {}).get("observation") or {}
    value = {**enrollment, **observation}
    checked = value.get("checked_on")
    try:
        stale = not checked or (today - date.fromisoformat(checked)).days not in range(15)
        closed = value.get("closes_on") and date.fromisoformat(value["closes_on"]) < today
        future = value.get("opens_on") and date.fromisoformat(value["opens_on"]) > today
    except (ValueError, TypeError):
        stale, closed, future = True, False, False
    status = value.get("status", "unknown")
    if stale or value.get("unavailable") or future:
        status = "unknown"
    elif closed:
        status = "closed"
    return {**value, "status": status, "stale": stale}
