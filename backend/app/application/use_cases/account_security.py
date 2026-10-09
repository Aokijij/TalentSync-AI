import hmac
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import quote

from app.application.errors import UseCaseError
from app.application.use_cases.events import record_event
from app.domain.entities.enums import UserRole
from app.domain.services.access_policy import requires_mfa_setup
from app.domain.services.authentication import (
    generate_totp_secret,
    token_digest,
    verify_totp,
)


def _password(user, password, security):
    if not security.verify_password(password, user.password_hash):
        raise UseCaseError(status_code=401, detail="Credenciales inválidas")


def _mfa(db, user, code, security):
    if not user.mfa_enabled:
        return
    counter = verify_totp(security.decrypt_secret(user.mfa_secret), code or "", user.mfa_last_counter)
    if counter is not None:
        if db.accounts.claim_mfa(user.id, user.mfa_last_counter, counter):
            user.mfa_last_counter = counter
            return
        raise UseCaseError(status_code=401, detail="El código ya fue utilizado")
    digest = token_digest(code or "")
    if any(hmac.compare_digest(value, digest) for value in user.recovery_codes or []):
        remaining = [value for value in user.recovery_codes if not hmac.compare_digest(value, digest)]
        counter = max(int(time.time() // 30), (user.mfa_last_counter or 0) + 1)
        if db.accounts.claim_mfa(user.id, user.mfa_last_counter, counter, remaining):
            user.recovery_codes = remaining
            user.mfa_last_counter = counter
            return
        raise UseCaseError(status_code=401, detail="El código ya fue utilizado")
    raise UseCaseError(status_code=401, detail="Código de autenticación inválido o ya utilizado")


def create_session(db, payload, security, *, admin=False, user_agent="", company_mfa_required=True, admin_mfa_required=True):
    user = db.users.find_by_email(payload["email"])
    if user is None:
        # Perform equivalent password work for unknown accounts.
        security.verify_password(payload["password"], security.hash_password("unavailable-account"))
        raise UseCaseError(status_code=401, detail="Credenciales inválidas")
    _password(user, payload["password"], security)
    if (user.role == UserRole.ADMIN) != admin:
        raise UseCaseError(status_code=401, detail="Credenciales inválidas para este acceso")
    if payload.get("portal") and user.role.value != payload["portal"]:
        raise UseCaseError(status_code=401, detail="Esta cuenta no pertenece a este acceso. Utiliza el portal de tu rol.")
    review = user.role == UserRole.ADMIN and not admin_mfa_required
    if user.mfa_enabled and not review and not payload.get("code"):
        return {"mfa_required": True}
    if not review:
        _mfa(db, user, payload.get("code"), security)
    return issue_session(db, user, remember=payload.get("remember"), user_agent=user_agent, company_mfa_required=company_mfa_required, admin_mfa_required=admin_mfa_required)


def issue_session(db, user, *, remember=False, user_agent="", authentication_method="password", authentication_authority="", company_mfa_required=True, admin_mfa_required=True):
    # Callers must authenticate the user and complete any configured MFA first.
    token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    now = datetime.utcnow()
    remember = bool(remember) and user.role == UserRole.CANDIDATE
    lifetime = timedelta(days=30) if remember else timedelta(hours=8)
    session = db.accounts.new_session(user_id=user.id, token_hash=token_digest(token),
        csrf_hash=token_digest(csrf), user_agent=user_agent[:255], created_at=now,
          last_seen_at=now, expires_at=now + lifetime, mfa_verified=user.mfa_enabled and not (user.role == UserRole.ADMIN and not admin_mfa_required), authentication_method=authentication_method,
          authentication_authority=authentication_authority)
    db.add(session)
    db.flush()
    record_event(db, "session.created", "user", user.id, actor_user_id=user.id, details={"session_id": session.id})
    db.commit()
    return {"token": token, "csrf": csrf, "remember": remember, "user": user,
            "mfa_setup_required": requires_mfa_setup(user.role, company_mfa_required, admin_mfa_required) and not user.mfa_enabled}


def resolve_session(db, token, *, csrf=None, mutation=False):
    session = db.accounts.session_by_hash(token_digest(token))
    now = datetime.utcnow()
    if session is None or session.revoked_at or session.expires_at <= now:
        raise UseCaseError(status_code=401, detail="Tu sesión venció o fue cerrada")
    user = db.users.get(session.user_id)
    if user is None:
        raise UseCaseError(status_code=401, detail="Sesión inválida")
    idle = timedelta(days=7) if user.role == UserRole.CANDIDATE else timedelta(minutes=30)
    if session.last_seen_at + idle <= now:
        raise UseCaseError(status_code=401, detail="La sesión venció por inactividad")
    if mutation and not hmac.compare_digest(session.csrf_hash, token_digest(csrf or "")):
        raise UseCaseError(status_code=403, detail="La solicitud requiere un token CSRF válido")
    if now - session.last_seen_at > timedelta(minutes=1):
        session.last_seen_at = now
        db.commit()
    return user, session


def revoke_session(db, user, session_id):
    selected = next((row for row in db.accounts.sessions_for_user(user.id) if row.id == session_id), None)
    if selected is None:
        raise UseCaseError(status_code=404, detail="Sesión no encontrada")
    selected.revoked_at = datetime.utcnow()
    record_event(db, "session.revoked", "user", user.id, actor_user_id=user.id, details={"session_id": selected.id})
    db.commit()


def request_action(db, email, purpose, *, app_url, mail_enabled, target_email=None, delivery_mode="local"):
    if not mail_enabled:
        raise UseCaseError(status_code=503, detail="El servicio de correo no está configurado")
    user = db.users.find_by_email(email)
    if user is not None:
        token = secrets.token_urlsafe(40)
        db.add(db.accounts.new_token(user_id=user.id, token_hash=token_digest(token), purpose=purpose,
                                    target_email=target_email, expires_at=datetime.utcnow() + timedelta(minutes=30)))
        labels = {"verify": "Confirma tu correo", "reset": "Recupera tu acceso", "email": "Confirma tu nuevo correo"}
        link = f"{app_url.rstrip('/')}/cuenta/confirmar?purpose={purpose}&token={quote(token)}"
        db.add(db.accounts.new_message(recipient=target_email or user.email, subject=labels[purpose],
            delivery_state=delivery_mode, expires_at=datetime.utcnow() + timedelta(minutes=30),
            body=f"{labels[purpose]} en TalentSync: {link}\nEste enlace vence en 30 minutos y solo puede usarse una vez. Si no lo solicitaste, ignora este mensaje."))
        db.commit()
    return {"message": "Si la cuenta corresponde, encontrarás las instrucciones en su correo."}


def complete_action(db, token, purpose, *, password=None, security):
    row = db.accounts.token_by_hash(token_digest(token), purpose)
    if row is None or not db.accounts.claim_token(row.id):
        raise UseCaseError(status_code=400, detail="El enlace venció o ya fue utilizado")
    user = db.users.get(row.user_id)
    if purpose == "reset":
        if not password or len(password) < 12 or len(password.encode()) > 72:
            raise UseCaseError(status_code=422, detail="Usa una contraseña de al menos 12 caracteres y hasta 72 bytes")
        user.password_hash = security.hash_password(password)
        db.accounts.revoke_sessions(user.id)
    elif purpose == "verify":
        if row.target_email and row.target_email != user.email:
            raise UseCaseError(status_code=400, detail="El enlace corresponde a otro correo")
        user.email_verified = True
    elif purpose == "email":
        if db.users.find_by_email(row.target_email):
            raise UseCaseError(status_code=409, detail="No se puede utilizar ese correo")
        user.email = row.target_email
        user.email_verified = True
        db.accounts.revoke_sessions(user.id)
    else:
        raise UseCaseError(status_code=422, detail="Acción desconocida")
    record_event(db, f"account.{purpose}", "user", user.id, actor_user_id=user.id)
    db.commit()
    return {"message": "Cambio confirmado. Puedes continuar o iniciar sesión de nuevo."}


def start_mfa(db, user, password, security):
    _password(user, password, security)
    if user.mfa_enabled:
        raise UseCaseError(status_code=409, detail="La autenticación ya está activada")
    secret = generate_totp_secret()
    user.mfa_secret = security.encrypt_secret(secret)
    user.mfa_last_counter = None
    db.commit()
    return {"secret": secret, "uri": f"otpauth://totp/TalentSync:{quote(user.email)}?secret={secret}&issuer=TalentSync&algorithm=SHA1&digits=6&period=30"}


def confirm_mfa(db, user, session, code, security):
    if user.mfa_enabled or not user.mfa_secret:
        raise UseCaseError(status_code=409, detail="Inicia una configuración nueva")
    counter = verify_totp(security.decrypt_secret(user.mfa_secret), code)
    if counter is None:
        raise UseCaseError(status_code=422, detail="El código no es válido")
    recovery = [secrets.token_hex(8) for _ in range(8)]
    user.mfa_enabled = True
    user.mfa_last_counter = counter
    user.recovery_codes = [token_digest(value) for value in recovery]
    session.mfa_verified = True
    db.accounts.revoke_sessions(user.id, except_id=session.id)
    record_event(db, "account.mfa_enabled", "user", user.id, actor_user_id=user.id)
    db.commit()
    return {"recovery_codes": recovery}


def disable_mfa(db, user, session, payload, security):
    if user.role != UserRole.CANDIDATE:
        raise UseCaseError(status_code=403, detail="La autenticación es obligatoria para este rol")
    _password(user, payload["password"], security)
    _mfa(db, user, payload["code"], security)
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_last_counter = None
    user.recovery_codes = []
    db.accounts.revoke_sessions(user.id, except_id=session.id)
    record_event(db, "account.mfa_disabled", "user", user.id, actor_user_id=user.id)
    db.commit()


def privacy(db, user, preferences=None):
    defaults = {"share_evidence": True, "notify_new_skills": False, "personalize_recommendations": False}
    if preferences is not None:
        if preferences.keys() - defaults.keys() or any(type(v) is not bool for v in preferences.values()):
            raise UseCaseError(status_code=422, detail="Preferencias inválidas")
        previously_personalized = (user.privacy_preferences or {}).get("personalize_recommendations", False)
        user.privacy_preferences = {**defaults, **user.privacy_preferences, **preferences}
        if previously_personalized and not user.privacy_preferences["personalize_recommendations"]:
            db.personalization.purge_user(user.id)
        record_event(db, "account.privacy_updated", "user", user.id, actor_user_id=user.id)
        db.commit()
    return {**defaults, **(user.privacy_preferences or {})}
