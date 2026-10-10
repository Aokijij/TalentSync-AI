import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta

from app.application.errors import UseCaseError
from app.application.use_cases.account_security import _mfa, issue_session
from app.application.use_cases.events import record_event
from app.domain.entities.enums import UserRole
from app.domain.services.authentication import token_digest
from app.domain.services.corporate_identity import PROVIDERS, entra_subject


def begin(db, gateway, security, *, provider="workspace", authority=""):
    if provider not in PROVIDERS or not gateway.configured(provider):
        raise UseCaseError(status_code=503, detail="El acceso corporativo no está configurado")
    state, browser, verifier = (secrets.token_urlsafe(48) for _ in range(3))
    digest = token_digest(state)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    url = gateway.authorization_url(provider, state, challenge, digest)
    db.accounts.purge_oauth_attempts()
    db.add(db.accounts.new_oauth_attempt(provider=provider, purpose="admin", state_hash=digest,
        browser_hash=token_digest(browser), verifier_cipher=security.encrypt_secret(json.dumps({"verifier": verifier, "authority": authority})),
        expires_at=datetime.utcnow() + timedelta(minutes=10)))
    db.commit()
    return {"url": url, "browser": browser}


def bound_admin(db, subject, provider="workspace"):
    if provider not in PROVIDERS:
        raise UseCaseError(status_code=403, detail="Proveedor administrativo inválido")
    identity = db.accounts.identity(provider, subject)
    user = db.users.get(identity.user_id) if identity else None
    if user is None or user.role != UserRole.ADMIN:
        raise UseCaseError(status_code=403, detail="La cuenta corporativa no tiene acceso administrativo aprovisionado")
    return user


def callback(db, state, browser, code, gateway, security, *, user_agent="", domain="", provider="workspace", authority="", mfa_review=False):
    if provider not in PROVIDERS or not gateway.configured(provider):
        raise UseCaseError(status_code=503, detail="El acceso corporativo no está configurado")
    row = db.accounts.oauth_attempt(token_digest(state))
    if (not browser or row is None or row.provider != provider or row.purpose != "admin"
            or row.used_at or row.expires_at <= datetime.utcnow()
            or not hmac.compare_digest(row.browser_hash, token_digest(browser))):
        raise UseCaseError(status_code=400, detail="El acceso venció o corresponde a otro navegador")
    try:
        transaction = json.loads(security.decrypt_secret(row.verifier_cipher))
        verifier = transaction["verifier"]
        if transaction["authority"] != authority or not isinstance(verifier, str):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise UseCaseError(status_code=400, detail="La configuración corporativa cambió; inicia el acceso de nuevo") from None
    nonce = row.state_hash
    if not db.accounts.claim_oauth_attempt(row.id):
        raise UseCaseError(status_code=400, detail="El acceso ya fue utilizado")
    db.commit()
    if not code:
        raise UseCaseError(status_code=400, detail="El acceso corporativo fue cancelado")
    identity = gateway.exchange(provider, code, verifier, nonce)
    user = bound_admin(db, identity["subject"], provider)
    if user.mfa_enabled and not mfa_review:
        pending = secrets.token_urlsafe(48)
        db.add(db.accounts.new_token(user_id=user.id, token_hash=token_digest(pending), purpose="admin_sso_mfa",
            context={"subject": identity["subject"], "domain": domain, "provider": provider, "authority": authority}, expires_at=datetime.utcnow() + timedelta(minutes=5)))
        db.commit()
        return {"pending": pending, "mfa_required": True}
    # First access can only reach account security until platform MFA is configured.
    return issue_session(db, user, user_agent=user_agent, authentication_method=provider, authentication_authority=authority, mfa_review=mfa_review)


def complete(db, pending, code, security, *, user_agent="", domain="", provider="workspace", authority=""):
    row = db.accounts.token_by_hash(token_digest(pending or ""), "admin_sso_mfa")
    if (row is None or row.used_at or row.expires_at <= datetime.utcnow() or (row.context or {}).get("domain") != domain
            or (row.context or {}).get("provider") != provider or (row.context or {}).get("authority") != authority):
        raise UseCaseError(status_code=401, detail="Vuelve a iniciar el acceso corporativo")
    subject = (row.context or {}).get("subject")
    user = bound_admin(db, subject, provider)
    if user.id != row.user_id or not user.mfa_enabled:
        raise UseCaseError(status_code=401, detail="Vuelve a iniciar el acceso corporativo")
    _mfa(db, user, code, security)
    if not db.accounts.claim_token(row.id):
        raise UseCaseError(status_code=401, detail="El acceso ya fue utilizado")
    return issue_session(db, user, user_agent=user_agent, authentication_method=provider, authentication_authority=authority)


def provision(db, email, subject=None, *, provider="workspace"):
    if provider not in PROVIDERS or provider == "entra" and subject and not entra_subject(subject):
        raise UseCaseError(status_code=422, detail="Proveedor o sujeto inválido; Entra requiere tenant UUID:object UUID en minúsculas")
    user = db.users.find_by_email(email.casefold())
    if user is None or user.role != UserRole.ADMIN:
        raise UseCaseError(status_code=422, detail="Se requiere una cuenta administradora existente; no se crean ni elevan roles")
    existing = [row for row in db.accounts.identities_for_user(user.id) if row.provider == provider]
    if subject:
        if len(subject) > 255 or not subject.strip() or subject != subject.strip():
            raise UseCaseError(status_code=422, detail="Sujeto corporativo inválido")
        if db.accounts.identity(provider, subject) or existing:
            raise UseCaseError(status_code=409, detail="Ya existe un vínculo; revócalo antes de reemplazarlo")
        db.add(db.accounts.new_identity(user_id=user.id, provider=provider, subject=subject))
    else:
        for identity in existing:
            db.delete(identity)
    db.accounts.revoke_sessions(user.id)
    record_event(db, "account.admin_sso_provisioned", "user", user.id,
                 details={"source": "local_cli", "status": "bound" if subject else "revoked"})
    db.commit()
