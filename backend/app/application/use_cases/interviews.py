from datetime import datetime, timedelta
from uuid import uuid4

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.application.use_cases.organizations import context
from app.domain.entities.enums import UserRole


def allowed(db, user, application):
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.CANDIDATE:
        return application.user_id == user.id
    company = context(db, user)
    if application.job.company_id != company.id:
        return False
    member = db.organizations.member_for_user(user.id)
    if company.owner_user_id == user.id:
        return True
    return bool(member and member.active and (member.role == "recruiter" or application.job_id in member.assigned_job_ids))


def active(room):
    application = room.application
    return not room.closed and not application.released_at and application.status not in {"rejected", "hired"} and (not application.job.blind_hiring or application.identity_revealed_at is not None)


def room_view(room):
    return {"id": room.id, "application_id": room.application_id, "title": room.title,
        "code": room.code, "whiteboard": room.whiteboard, "version": room.version, "closed": room.closed,
        "active": active(room), "created_at": room.created_at, "updated_at": room.updated_at,
        "execution_enabled": False, "video_mode": "local_webrtc_no_relay"}


def get(db, user, room_id, *, writable=False):
    room = db.interviews.get(room_id)
    if room is None or not allowed(db, user, room.application):
        raise UseCaseError(status_code=404, detail="Sala no disponible para esta cuenta")
    if writable and not active(room):
        raise UseCaseError(status_code=409, detail="La sala o el proceso están cerrados")
    return room


def rooms(db, user):
    return [room_view(row) for row in db.interviews.rooms() if allowed(db, user, row.application)]


def create(db, user, application_id, title):
    application = db.applications.get(application_id)
    if user.role == UserRole.CANDIDATE or application is None or not allowed(db, user, application):
        raise UseCaseError(status_code=403, detail="Solo el equipo asignado puede preparar una entrevista")
    if application.status != "technical_interview":
        raise UseCaseError(status_code=409, detail="Avanza el proceso a entrevista técnica antes de crear la sala")
    existing = db.interviews.for_application(application_id)
    if existing:
        return room_view(existing)
    room = db.interviews.new_room(id=uuid4().hex, application_id=application_id, creator_user_id=user.id,
        title=title, code="", whiteboard=[], closed=False)
    db.add(room)
    record_event(db, "interview.room_created", "application", application.id, actor_user_id=user.id)
    db.add(db.notifications.new(user_id=application.user_id, type="application_interview", title="Sala de entrevista preparada",
        body="Tu proceso tiene una sala con editor y pizarra compartidos.", action_url=f"/entrevistas/{room.id}"))
    db.commit()
    return room_view(room)


def save(db, user, room_id, payload):
    room = get(db, user, room_id, writable=True)
    if room.version != payload["expected_version"]:
        raise UseCaseError(status_code=409, detail="Otra persona publicó cambios; conserva tu borrador y carga la versión compartida")
    room.code = payload["code"]
    room.whiteboard = payload["whiteboard"]
    # Force a version increment even for an identical document.
    room.updated_at = datetime.utcnow()
    db.commit()
    return room_view(room)


def close(db, user, room_id):
    room = get(db, user, room_id)
    if user.role == UserRole.CANDIDATE:
        raise UseCaseError(status_code=403, detail="Solo el equipo puede cerrar la sala")
    room.closed = True
    db.interviews.cleanup(datetime.utcnow(), room.id)
    record_event(db, "interview.room_closed", "application", room.application_id, actor_user_id=user.id)
    db.commit()
    return room_view(room)


def connect(db, user, room_id):
    get(db, user, room_id, writable=True)
    now = datetime.utcnow()
    db.interviews.cleanup(now)
    participants = db.interviews.participants(room_id)
    occupied = {row.slot for row in participants}
    free = next((slot for slot in range(2) if slot not in occupied), None)
    if free is None:
        raise UseCaseError(status_code=409, detail="La videollamada admite dos pestañas; desconecta una o espera 90 segundos")
    row = db.interviews.new_participant(id=uuid4().hex, room_id=room_id, user_id=user.id, slot=free, expires_at=now + timedelta(seconds=90))
    db.add(row)
    db.commit()
    return {"participant_id": row.id}


def participant(db, user, room_id, participant_id):
    get(db, user, room_id, writable=True)
    row = db.interviews.participant(participant_id)
    if row is None or row.room_id != room_id or row.user_id != user.id or row.expires_at <= datetime.utcnow():
        raise UseCaseError(status_code=404, detail="Conexión caducada; vuelve a conectar")
    return row


def poll(db, user, room_id, participant_id, after_id):
    row = participant(db, user, room_id, participant_id)
    now = datetime.utcnow()
    row.expires_at = now + timedelta(seconds=90)
    db.interviews.cleanup(now)
    signals = db.interviews.signals(room_id, participant_id, after_id, now)
    result = {"participants": [{"id": item.id} for item in db.interviews.participants(room_id)],
        "signals": [{"id": item.id, "sender_id": item.sender_id, "kind": item.kind, "payload": item.payload} for item in signals]}
    db.commit()
    return result


def signal(db, user, room_id, participant_id, payload):
    participant(db, user, room_id, participant_id)
    target = db.interviews.participant(payload["recipient_id"])
    now = datetime.utcnow()
    if target is None or target.id == participant_id or target.room_id != room_id or target.expires_at <= now:
        raise UseCaseError(status_code=404, detail="El otro participante se desconectó")
    db.add(db.interviews.new_signal(room_id=room_id, sender_id=participant_id, recipient_id=target.id,
        kind=payload["kind"], payload=payload["payload"], expires_at=now + timedelta(seconds=60)))
    db.commit()
    return {"sent": True}


def disconnect(db, user, room_id, participant_id):
    get(db, user, room_id)
    row = db.interviews.participant(participant_id)
    if row and row.room_id == room_id and row.user_id == user.id:
        db.delete(row)
        db.commit()
    return {"disconnected": True}
