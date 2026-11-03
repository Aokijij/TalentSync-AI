from datetime import datetime, timedelta, timezone

FINAL = {"rejected", "accepted", "hired"}
PAUSE_WORKDAYS = 3
EXTENSION_WORKDAYS = 7
EXTENSION_LIMIT = 1


def add_workdays(value, days):
    """Platform working days are Monday–Friday in Colombia, without holidays."""
    local = value.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-5)))
    direction = 1 if days >= 0 else -1
    for _ in range(abs(days)):
        local += timedelta(days=direction)
        while local.weekday() >= 5:
            local += timedelta(days=direction)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def reset_response(row, due):
    row.response_due_at = due
    row.reminder_sent_at = None
    row.response_overdue_at = None
    row.response_paused_at = None
    row.deadline_extension_count = 0


def interview_deadline(row):
    if row.interview_at and not row.released_at and str(row.status) not in FINAL:
        end = row.interview_at + timedelta(minutes=(row.interview_details or {}).get("minutes", 45))
        return add_workdays(end, row.job.response_days)
    return None


def response_state(row, now=None):
    now = now or datetime.utcnow()
    if row.released_at or str(row.status) in FINAL:
        return "closed"
    if getattr(row, "response_paused_at", None):
        return "paused"
    if row.response_due_at is None:
        return "none"
    return "overdue" if row.response_due_at <= now else "on_time"


def deadline_view(row, now=None):
    overdue = getattr(row, "response_overdue_at", None)
    return {"response_state": response_state(row, now), "response_overdue_at": overdue,
            "response_paused_at": getattr(row, "response_paused_at", None),
            "deadline_extension_count": getattr(row, "deadline_extension_count", 0) or 0,
            "pause_due_at": add_workdays(overdue, PAUSE_WORKDAYS) if overdue and not getattr(row, "response_paused_at", None) else None,
            "deadline_policy": {"calendar": "weekdays", "pause_workdays": PAUSE_WORKDAYS,
                                "extension_workdays": EXTENSION_WORKDAYS, "extension_limit": EXTENSION_LIMIT}}
