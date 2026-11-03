import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from html import escape
from uuid import uuid4

from app.application.calendar_errors import CalendarProviderError
from app.application.errors import UseCaseError
from app.application.use_cases.integration_observations import record
from app.application.use_cases.workflow import FINAL, accessible_application
from app.domain.services.authentication import token_digest

ERRORS = {"missing": "El evento ya no existe en Google. Añade de nuevo la entrevista.", "authorization": "La autorización venció o fue revocada. Vuelve a conectar Google Calendar.", "temporary": "Google Calendar no respondió. Se volverá a intentar.", "configuration": "La conexión de Google Calendar no está configurada.", "access": "Ya no tienes acceso a este proceso; la sincronización se ha detenido."}


def status(db, user, gateway):
    connection = db.calendars.connection(user.id)
    return {"provider": "google", "configured": gateway.configured, "connected": connection is not None,
            "needs_reconnect": bool(connection and connection.last_error == "authorization"), "connected_at": connection.connected_at if connection else None, "error": ERRORS.get(connection.last_error, "") if connection else "",
            "note": "Solo se sincronizan entrevistas que elijas. No se añaden invitados ni se envían notas internas."}


def begin(db, user, session, gateway, security):
    if not session or session.user_id != user.id:
        raise UseCaseError(status_code=403, detail="Se requiere tu sesión del navegador")
    if not gateway.configured:
        raise UseCaseError(status_code=503, detail=ERRORS["configuration"])
    state, browser, verifier = (secrets.token_urlsafe(48) for _ in range(3))
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    db.add(db.accounts.new_oauth_attempt(provider="calendar_google", purpose="calendar", link_user_id=user.id, link_session_id=session.id,
        state_hash=token_digest(state), browser_hash=token_digest(browser), verifier_cipher=security.encrypt_secret(verifier), expires_at=datetime.utcnow() + timedelta(minutes=10)))
    db.commit()
    return {"url": gateway.authorization_url(state, challenge), "browser": browser}


def callback(db, user, session, state, browser, code, gateway, security):
    row = db.accounts.oauth_attempt(token_digest(state))
    if (not row or row.provider != "calendar_google" or row.purpose != "calendar" or row.used_at or row.expires_at <= datetime.utcnow()
            or row.link_user_id != user.id or row.link_session_id != session.id or not browser or not hmac.compare_digest(row.browser_hash, token_digest(browser))):
        raise UseCaseError(status_code=400, detail="La autorización venció o corresponde a otra sesión", code="expired")
    verifier = security.decrypt_secret(row.verifier_cipher)
    if not db.accounts.claim_oauth_attempt(row.id):
        raise UseCaseError(status_code=400, detail="La autorización ya se utilizó")
    db.commit()
    if not code:
        raise UseCaseError(status_code=400, detail="No se autorizó el calendario", code="cancelled")
    try:
        refresh = gateway.exchange(code, verifier)
    except CalendarProviderError as failure:
        record(db, "calendar", "provider_error")
        raise UseCaseError(status_code=503, detail=ERRORS.get(failure.code, ERRORS["temporary"]), code=failure.code) from None
    db.calendars.connect(user.id, security.encrypt_secret(refresh))
    record(db, "calendar", commit=False, operation="calendar_connect")
    db.commit()
    return {"connected": True}


def event_status(db, user, application_id):
    application = accessible_application(db, user, application_id)
    row = db.calendars.event(user.id, application_id)
    return {"enabled": row is not None, "state": "needs_sync" if row and row.state in {"synced", "cancelled"} and row.application_version != application.version else row.state if row else "none", "minutes": (application.interview_details or {}).get("minutes", row.minutes if row else 45),
            "last_synced_at": row.last_synced_at if row else None, "error": ERRORS.get(row.error_code, "") if row else ""}


def enqueue(db, user, application_id, minutes, gateway):
    application = accessible_application(db, user, application_id)
    if not gateway.configured or not db.calendars.connection(user.id):
        raise UseCaseError(status_code=409, detail="Conecta Google Calendar desde Seguridad antes de sincronizar")
    if not application.interview_at or application.released_at or application.status in FINAL:
        raise UseCaseError(status_code=409, detail="No hay una entrevista activa para sincronizar")
    if application.interview_at <= datetime.utcnow():
        raise UseCaseError(status_code=409, detail="La fecha de la entrevista ya pasó")
    minutes = (application.interview_details or {}).get("minutes", minutes)
    row = db.calendars.event(user.id, application_id)
    if row is None:
        row = db.calendars.new_event(id=uuid4().hex, user_id=user.id, application_id=application_id, remote_id="ts" + uuid4().hex, minutes=minutes)
        db.add(row)
    else:
        if not db.calendars.claim(row.id, secrets.token_urlsafe(24), datetime.utcnow()):
            raise UseCaseError(status_code=409, detail="Hay una sincronización en curso. Espera unos segundos antes de cambiar la copia.")
        db.refresh(row)
        if row.state == "cancelled" or row.error_code == "missing":
            row.remote_id, row.application_version = "ts" + uuid4().hex, 0
        row.minutes, row.state, row.error_code, row.next_attempt_at = minutes, "pending", "", None
        row.lease_token, row.lease_until = "", None
    db.commit()
    return event_status(db, user, application_id)


def process_event(db, row, user, gateway, security, *, public_app_url):
    lease, now = secrets.token_urlsafe(24), datetime.utcnow()
    if not db.calendars.claim(row.id, lease, now):
        return False
    db.commit()
    db.refresh(row)
    connection = db.calendars.connection(user.id)
    if not connection:
        row.lease_token, row.lease_until = "", None
        db.commit()
        return False
    try:
        application = accessible_application(db, user, row.application_id)
        version = application.version
        active = bool(application.interview_at and not application.released_at and application.status not in FINAL)
        event = None
        if active:
            start = application.interview_at.replace(tzinfo=timezone.utc)
            details = application.interview_details or {}
            row.minutes = details.get("minutes", row.minutes)
            end = start + timedelta(minutes=row.minutes)
            modality = "Virtual" if details.get("mode") == "virtual" else "Presencial" if details.get("mode") == "in_person" else "Modalidad por confirmar"
            description = "\n".join(escape(text) for text in [f"Empresa: {application.job.company.name}", f"Modalidad: {modality}", f"Duración: {row.minutes} minutos", details.get("location", "Lugar o enlace por confirmar"), details.get("instructions", ""), f"Consulta el proceso: {public_app_url.rstrip('/')}/procesos/{application.id}"] if text)
            event = {"summary": f"Entrevista · {application.job.title}"[:200], "description": description, "location": details.get("location", ""),
                     "visibility": "private", "start": {"dateTime": start.isoformat(), "timeZone": "America/Bogota"}, "end": {"dateTime": end.isoformat(), "timeZone": "America/Bogota"},
                     "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 30}]}}
        if active and row.state == "cancelled":
            row.remote_id, row.application_version, row.state = "ts" + uuid4().hex, 0, "pending"
            db.commit()
        try:
            refresh = security.decrypt_secret(connection.refresh_cipher)
        except (ValueError, TypeError):
            raise CalendarProviderError("authorization") from None
        access, rotated = gateway.refresh(refresh)
        if rotated:
            connection.refresh_cipher = security.encrypt_secret(rotated)
        gateway.sync(access, row.remote_id, event, create=row.application_version == 0)
        row.application_version, row.state, row.error_code, row.attempts, row.last_synced_at = version, "synced" if active else "cancelled", "", 0, now
        row.next_attempt_at, connection.last_error = None, ""
        record(db, "calendar", commit=False, operation="calendar_sync")
    except (CalendarProviderError, UseCaseError) as failure:
        code = failure.code if isinstance(failure, CalendarProviderError) else "access"
        row.error_code, row.attempts = code, row.attempts + 1
        row.state = "retry" if code == "temporary" and row.attempts < 5 else "failed"
        row.next_attempt_at = now + timedelta(seconds=min(60 * 2 ** min(row.attempts, 6), 3600)) if row.state == "retry" else None
        if code == "authorization":
            connection.last_error = code
        if isinstance(failure, CalendarProviderError):
            record(db, "calendar", "provider_error", commit=False)
    finally:
        row.lease_token, row.lease_until = "", None
        db.commit()
    return True


def disconnect(db, user):
    db.calendars.disconnect(user.id)
    db.commit()
    return {"message": "Calendario desconectado. Se detuvo la sincronización; los eventos existentes en Google Calendar se conservan y dejan de actualizarse."}


def synchronize(db, user, application_id, minutes, gateway, security, public_app_url):
    enqueue(db, user, application_id, minutes, gateway)
    row = db.calendars.event(user.id, application_id)
    process_event(db, row, user, gateway, security, public_app_url=public_app_url)
    return event_status(db, user, application_id)
