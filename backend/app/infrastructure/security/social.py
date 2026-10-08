"""Fixed-endpoint OAuth adapters. Tokens exist only for the duration of exchange."""
import hmac
import re
from urllib.parse import urlencode, urlsplit

import httpx
import jwt
from email_validator import EmailNotValidError, validate_email

from app.application.errors import UseCaseError

OIDC = {
    "workspace": {"authorize": "https://accounts.google.com/o/oauth2/v2/auth",
                  "token": "https://oauth2.googleapis.com/token", "keys": "https://www.googleapis.com/oauth2/v3/certs",
                  "issuers": ["accounts.google.com", "https://accounts.google.com"]},
    "google": {"authorize": "https://accounts.google.com/o/oauth2/v2/auth",
               "token": "https://oauth2.googleapis.com/token", "keys": "https://www.googleapis.com/oauth2/v3/certs",
               "issuers": ["accounts.google.com", "https://accounts.google.com"]},
    "linkedin": {"authorize": "https://www.linkedin.com/oauth/v2/authorization",
                 "token": "https://www.linkedin.com/oauth/v2/accessToken", "keys": "https://www.linkedin.com/oauth/openid/jwks",
                 "issuers": ["https://www.linkedin.com"]},
}


class SocialIdentityProvider:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport

    def configured(self, provider):
        if provider not in {"github", *OIDC} or not self.settings.session_auth_enabled:
            return False
        try:
            url = urlsplit(self.settings.public_app_url)
            if not url.hostname:
                return False
            _ = url.port
        except ValueError:
            return False
        if provider == "workspace" and not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", getattr(self.settings, "workspace_domain", "")):
            return False
        secure_url = url.scheme == "https" or (
            self.settings.environment == "development" and url.scheme == "http"
            and url.hostname in {"localhost", "127.0.0.1", "::1"})
        return bool(secure_url and not url.username and not url.password and not url.query
                    and not url.fragment and url.path in {"", "/"}
                    and (provider != "linkedin" or url.scheme == "https")
                    and getattr(self.settings, f"oauth_{provider}_client_id", "")
                    and getattr(self.settings, f"oauth_{provider}_client_secret", ""))

    def _configuration(self, provider):
        if not self.configured(provider):
            raise UseCaseError(status_code=503, detail="El acceso social no está configurado")
        callback = "/api/v1/auth/admin-sso/callback" if provider == "workspace" else f"/api/v1/auth/social/{provider}/callback"
        return {"client_id": getattr(self.settings, f"oauth_{provider}_client_id"),
                "redirect_uri": f"{self.settings.public_app_url.rstrip('/')}{callback}"}

    def authorization_url(self, provider, state, challenge, nonce):
        params = {**self._configuration(provider), "state": state,
                  "code_challenge": challenge, "code_challenge_method": "S256", "response_type": "code"}
        if provider == "github":
            endpoint = "https://github.com/login/oauth/authorize"
            params.update(scope="read:user user:email")
        else:
            endpoint = OIDC[provider]["authorize"]
            params.update(scope="openid email profile", nonce=nonce)
            if provider in {"google", "workspace"}:
                params.update(prompt="select_account")
            if provider == "workspace":
                params.update(hd=self.settings.workspace_domain)
        return f"{endpoint}?{urlencode(params)}"

    @staticmethod
    def _json(response):
        response.raise_for_status()
        if len(response.content) > 1_000_000:
            raise ValueError("Oversized provider response")
        return response.json()

    def exchange(self, provider, code, verifier, nonce):
        params = {**self._configuration(provider), "code": code, "code_verifier": verifier,
                  "client_secret": getattr(self.settings, f"oauth_{provider}_client_secret"),
                  "grant_type": "authorization_code"}
        try:
            with httpx.Client(timeout=10, follow_redirects=False, transport=self.transport) as client:
                if provider == "github":
                    tokens = self._json(client.post("https://github.com/login/oauth/access_token", data=params,
                                                   headers={"Accept": "application/json"}))
                    token = tokens.get("access_token")
                    if not isinstance(token, str) or not token:
                        raise ValueError("Missing access token")
                    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
                    user = self._json(client.get("https://api.github.com/user", headers=headers))
                    emails = self._json(client.get("https://api.github.com/user/emails", headers=headers))
                    email = next((row["email"] for row in emails if row.get("primary") is True and row.get("verified") is True), None)
                    subject = str(user["id"]) if type(user.get("id")) is int and user["id"] > 0 else None
                    name = user.get("name") or user.get("login")
                else:
                    metadata = OIDC[provider]
                    tokens = self._json(client.post(metadata["token"], data=params))
                    id_token = tokens["id_token"]
                    header = jwt.get_unverified_header(id_token)
                    keys = self._json(client.get(metadata["keys"]))["keys"]
                    key = next(row for row in keys if row.get("kid") == header.get("kid") and row.get("kty") == "RSA")
                    user = jwt.decode(id_token, jwt.PyJWK.from_dict(key).key, algorithms=["RS256"],
                                      audience=params["client_id"], issuer=metadata["issuers"],
                                      options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]})
                    if not hmac.compare_digest(str(user["nonce"]), nonce):
                        raise ValueError("Unverified identity")
                    if user.get("azp") and user["azp"] != params["client_id"]:
                        raise ValueError("Unexpected authorized party")
                    if isinstance(user["aud"], list) and len(user["aud"]) > 1 and user.get("azp") != params["client_id"]:
                        raise ValueError("Ambiguous audience")
                    if provider == "linkedin":
                        token = tokens.get("access_token")
                        if not isinstance(token, str) or not token:
                            raise ValueError("Missing access token")
                        info = self._json(client.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {token}"}))
                        if info.get("sub") != user["sub"]:
                            raise ValueError("Userinfo subject mismatch")
                        user = {**user, **{key: info.get(key) for key in ("email", "email_verified", "name")}}
                    if user.get("email_verified") is not True:
                        raise ValueError("Unverified email")
                    if provider == "workspace" and user.get("hd") != self.settings.workspace_domain:
                        raise ValueError("Unexpected hosted domain")
                    email, subject, name = user.get("email"), user["sub"], user.get("name")
                if not isinstance(subject, str) or not subject or len(subject) > 255:
                    raise ValueError("Invalid subject")
                if not isinstance(email, str) or not email:
                    raise ValueError("Missing verified email")
                email = validate_email(email, check_deliverability=False).normalized.casefold()
                if len(email) > 255:
                    raise ValueError("Invalid email")
                return {"subject": subject, "email": email, "name": str(name or "Candidato")[:120]}
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError, StopIteration, jwt.PyJWTError, EmailNotValidError):
            # Do not include response bodies, authorization codes or tokens in logs/errors.
            raise UseCaseError(status_code=502, detail="No pudimos verificar tu identidad con el proveedor") from None
