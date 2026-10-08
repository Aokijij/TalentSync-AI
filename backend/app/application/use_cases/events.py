from app.application.ports.unit_of_work import UnitOfWork

# Event payloads are deliberately small. Never record credentials, CV contents,
# interview notes, or free-form answers in the audit stream.
ALLOWED_DETAILS = {
    "status", "previous_status", "stage", "previous_stage", "job_id",
    "company_id", "reason_code", "version", "position", "source", "role",
    "deadline", "assessment_id", "skill_id", "result", "session_id",
}


def record_event(db: UnitOfWork, event_type: str, entity_type: str,
                 entity_id: int | None, *, actor_user_id: int | None = None,
                 details: dict | None = None) -> None:
    values = details or {}
    unknown = values.keys() - ALLOWED_DETAILS
    if unknown:
        raise ValueError(f"Unsupported event details: {', '.join(sorted(unknown))}")
    if any(not isinstance(value, (str, int, float, bool, type(None))) for value in values.values()):
        raise ValueError("Event details must contain scalar values")
    db.add(db.events.new(
        actor_user_id=actor_user_id, event_type=event_type,
        entity_type=entity_type, entity_id=entity_id, details=dict(values),
    ))
