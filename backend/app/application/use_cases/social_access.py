import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.account_security import (
    _mfa,
    _password,
    issue_session,
    resolve_session,
)
from app.application.use_cases.events import record_event
from app.domain.entities.enums import UserRole
from app.domain.services.authentication import token_digest


def begin(db, provider, gateway, security, *, user=None, session=None, credentials=None, mfa_review=False):
    if provider not in {"github", "google", "linkedin"} or not gateway.configured(provider):
        raise UseCaseError(status_code=503, detail="El acceso social no está configurado")
    if user is not None:
        _reauthenticate(db, user, session, credentials, security, mfa_review=mfa_review)
        if any(row.provider == provider for row in db.accounts.identities_for_user(user.id)):
            raise UseCaseError(status_code=409, detail="Ese proveedor ya está vinculado a tu cuenta")
    state, browser, verifier = (secrets.token_urlsafe(48) for _ in range(3))
    digest = token_digest(state)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    url = gateway.authorization_url(provider, state, challenge, digest)
    db.accounts.purge_oauth_attempts()
    db.add(db.accounts.new_oauth_attempt(provider=provider, state_hash=digest, browser_hash=token_digest(browser),
        purpose="link" if user is not None else "login", link_user_id=user.id if user else None,
        link_session_id=session.id if session else None,
        verifier_cipher=security.encrypt_secret(verifier), expires_at=datetime.utcnow() + timedelta(minutes=10)))
    db.commit()
    return {"url": url, "browser": browser}


def callback(db, provider, state, browser, code, gateway, security, *, user_agent="", session_token=None, mfa_review=False):
    if not gateway.configured(provider):
        raise UseCaseError(status_code=503, detail="El acceso social no está configurado")
    row = db.accounts.oauth_attempt(token_digest(state))
    if (not browser or row is None or row.provider != provider or row.used_at
            or row.expires_at <= datetime.utcnow()
            or not hmac.compare_digest(row.browser_hash, token_digest(browser))):
        raise UseCaseError(status_code=400, detail="El acceso venció o corresponde a otro navegador")
    verifier = security.decrypt_secret(row.verifier_cipher)
    purpose, link_user_id, link_session_id, nonce = row.purpose, row.link_user_id, row.link_session_id, row.state_hash
    if purpose not in {"login", "link"}:
        raise UseCaseError(status_code=400, detail="Solicitud de acceso inválida")
    if purpose == "link":
        _link_context(db, session_token, link_user_id, link_session_id, mfa_review=mfa_review)
    if not db.accounts.claim_oauth_attempt(row.id):
        raise UseCaseError(status_code=400, detail="El acceso ya fue utilizado")
    db.commit()  # Consume before network I/O; provider failure must not make state reusable.
    if not code:
        raise UseCaseError(status_code=400, detail="No se autorizó el acceso social")
    identity_data = gateway.exchange(provider, code, verifier, nonce)
    if purpose == "link":
        user = _link_context(db, session_token, link_user_id, link_session_id, mfa_review=mfa_review)
        if (db.accounts.identity(provider, identity_data["subject"])
                or any(row.provider == provider for row in db.accounts.identities_for_user(user.id))):
            raise UseCaseError(status_code=409, detail="No se pueden unir ni reemplazar cuentas sociales existentes")
        db.add(db.accounts.new_identity(user_id=user.id, provider=provider, subject=identity_data["subject"]))
        record_event(db, "account.social_linked", "user", user.id, actor_user_id=user.id, details={"source": provider})
        db.commit()
        return {"linked": True}
    identity = db.accounts.identity(provider, identity_data["subject"])
    created = identity is None
    if identity:
        user = db.users.get(identity.user_id)
        if user is None or user.role != UserRole.CANDIDATE:
            raise UseCaseError(status_code=403, detail="Este acceso es exclusivo para candidatos")
        # The immutable provider subject identifies returning accounts, not changing email.
    else:
        if db.users.find_by_email(identity_data["email"]):
            raise UseCaseError(status_code=409, detail="Ya existe una cuenta con este correo. Ingresa con su método original.")
        user = db.users.new(name=identity_data["name"], email=identity_data["email"],
            role=UserRole.CANDIDATE, email_verified=True,
            password_hash=security.hash_password(secrets.token_urlsafe(48)))
        db.add(user)
        db.flush()
        db.add(db.profiles.new(user_id=user.id, skills=[]))
        db.add(db.accounts.new_identity(user_id=user.id, provider=provider, subject=identity_data["subject"]))
        record_event(db, "account.created", "user", user.id, actor_user_id=user.id,
                     details={"role": "candidate", "source": provider})
    if user.mfa_enabled and not mfa_review:
        pending = secrets.token_urlsafe(48)
        db.add(db.accounts.new_token(user_id=user.id, token_hash=token_digest(pending), purpose="social_mfa",
            expires_at=datetime.utcnow() + timedelta(minutes=5)))
        db.commit()
        return {"pending": pending, "mfa_required": True}
    return {**issue_session(db, user, user_agent=user_agent, mfa_review=mfa_review), "created": created}


def _reauthenticate(db, user, session, credentials, security, *, mfa_review=False):
    if user.role != UserRole.CANDIDATE or session is None or session.user_id != user.id:
        raise UseCaseError(status_code=403, detail="Se requiere una sesión de candidato")
    _password(user, (credentials or {}).get("password", ""), security)
    if not mfa_review:
        _mfa(db, user, (credentials or {}).get("code"), security)


def _link_context(db, session_token, user_id, session_id, *, mfa_review=False):
    user, session = resolve_session(db, session_token or "")
    db.refresh(user)
    if (user.id != user_id or session.id != session_id or user.role != UserRole.CANDIDATE
            or (user.mfa_enabled and not session.mfa_verified and not mfa_review)):
        raise UseCaseError(status_code=403, detail="La vinculación corresponde a otra sesión")
    return user


def identities(db, user):
    return [{"provider": row.provider, "created_at": row.created_at} for row in db.accounts.identities_for_user(user.id)]


def unlink(db, user, session, provider, credentials, security, *, mfa_review=False):
    selected = next((row for row in db.accounts.identities_for_user(user.id) if row.provider == provider), None)
    if selected is None:
        raise UseCaseError(status_code=404, detail="Proveedor no vinculado")
    _reauthenticate(db, user, session, credentials, security, mfa_review=mfa_review)
    db.delete(selected)
    db.accounts.cancel_social_access(user.id)
    db.accounts.revoke_sessions(user.id, except_id=session.id)
    record_event(db, "account.social_unlinked", "user", user.id, actor_user_id=user.id, details={"source": provider})
    db.commit()
    return {"message": "Proveedor desvinculado. Se cerraron las demás sesiones y se cancelaron los accesos sociales pendientes."}


def complete_mfa(db, pending, code, security, *, user_agent=""):
    row = db.accounts.token_by_hash(token_digest(pending or ""), "social_mfa")
    if row is None or row.used_at or row.expires_at <= datetime.utcnow():
        raise UseCaseError(status_code=401, detail="Vuelve a iniciar el acceso social")
    user = db.users.get(row.user_id)
    if user is None or user.role != UserRole.CANDIDATE or not user.mfa_enabled:
        raise UseCaseError(status_code=401, detail="Vuelve a iniciar el acceso social")
    _mfa(db, user, code, security)
    if not db.accounts.claim_token(row.id):
        raise UseCaseError(status_code=401, detail="El acceso ya fue utilizado")
    return issue_session(db, user, user_agent=user_agent)
