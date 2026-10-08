import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.account_security import _mfa, issue_session
from app.application.use_cases.events import record_event
from app.domain.entities.enums import UserRole
from app.domain.services.authentication import token_digest


def begin(db, provider, gateway, security):
    if not gateway.configured(provider):
        raise UseCaseError(status_code=503, detail="El acceso social no está configurado")
    state, browser, verifier = (secrets.token_urlsafe(48) for _ in range(3))
    digest = token_digest(state)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    url = gateway.authorization_url(provider, state, challenge, digest)
    db.accounts.purge_oauth_attempts()
    db.add(db.accounts.new_oauth_attempt(provider=provider, state_hash=digest, browser_hash=token_digest(browser),
        verifier_cipher=security.encrypt_secret(verifier), expires_at=datetime.utcnow() + timedelta(minutes=10)))
    db.commit()
    return {"url": url, "browser": browser}


def callback(db, provider, state, browser, code, gateway, security, *, user_agent=""):
    if not gateway.configured(provider):
        raise UseCaseError(status_code=503, detail="El acceso social no está configurado")
    row = db.accounts.oauth_attempt(token_digest(state))
    if (not browser or row is None or row.provider != provider or row.used_at
            or row.expires_at <= datetime.utcnow()
            or not hmac.compare_digest(row.browser_hash, token_digest(browser))):
        raise UseCaseError(status_code=400, detail="El acceso venció o corresponde a otro navegador")
    verifier = security.decrypt_secret(row.verifier_cipher)
    if not db.accounts.claim_oauth_attempt(row.id):
        raise UseCaseError(status_code=400, detail="El acceso ya fue utilizado")
    db.commit()  # Consume before network I/O; provider failure must not make state reusable.
    if not code:
        raise UseCaseError(status_code=400, detail="No se autorizó el acceso social")
    identity_data = gateway.exchange(provider, code, verifier, row.state_hash)
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
    if user.mfa_enabled:
        pending = secrets.token_urlsafe(48)
        db.add(db.accounts.new_token(user_id=user.id, token_hash=token_digest(pending), purpose="social_mfa",
            expires_at=datetime.utcnow() + timedelta(minutes=5)))
        db.commit()
        return {"pending": pending, "mfa_required": True}
    return {**issue_session(db, user, user_agent=user_agent), "created": created}


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
