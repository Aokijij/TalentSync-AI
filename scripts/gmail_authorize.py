"""One-time, send-only project mailbox authorization. Never imports the app or DB."""
import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import time
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx
from pydantic import EmailStr, TypeAdapter

ROOT = Path(__file__).resolve().parents[1]
SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
SCOPES = ("openid", "email", SEND_SCOPE)
ALLOWED_SCOPES = {*SCOPES, "https://www.googleapis.com/auth/userinfo.email"}


def private_write(path, text):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        file.write(text)
    if os.name == "nt":
        user = getpass.getuser()
        domain = os.environ.get("USERDOMAIN")
        identity = f"{domain}\\{user}" if domain else user
        result = subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", f"{identity}:(F)", "*S-1-5-18:(F)"], capture_output=True, check=False)
        if result.returncode:
            raise ValueError("private_file_permissions_failed")


def bounded_json(response):
    if response.status_code != 200:
        raise ValueError("google_authorization_failed")
    result = bytearray()
    for chunk in response.iter_bytes():
        result.extend(chunk)
        if len(result) > 16384:
            raise ValueError("google_response_too_large")
    value = json.loads(result)
    if not isinstance(value, dict):
        raise TypeError("invalid_google_response")
    return value


class Authorization:
    def __init__(self, credentials, sender, redirect):
        installed = credentials.get("installed", {})
        self.client_id = installed.get("client_id", "")
        self.client_secret = installed.get("client_secret", "")
        if not self.client_id.endswith(".apps.googleusercontent.com") or not self.client_secret:
            raise ValueError("desktop_oauth_client_required")
        self.sender = str(TypeAdapter(EmailStr).validate_python(sender)).casefold()
        parsed = urlsplit(redirect)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port or parsed.path != "/callback":
            raise ValueError("loopback_callback_required")
        self.redirect = redirect
        self.state = secrets.token_urlsafe(32)
        self.verifier = secrets.token_urlsafe(64)
        self.used = False
        self.refresh_expires_in = None

    def url(self):
        challenge = base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest()).rstrip(b"=").decode()
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": self.client_id, "redirect_uri": self.redirect, "response_type": "code",
            "scope": " ".join(SCOPES), "state": self.state, "code_challenge": challenge,
            "code_challenge_method": "S256", "access_type": "offline", "prompt": "consent select_account",
            "include_granted_scopes": "false", "login_hint": self.sender,
        })

    def complete(self, code, state, *, transport=None):
        if self.used or not state or not hmac.compare_digest(state, self.state) or not code or len(code) > 8192:
            raise ValueError("invalid_or_used_authorization")
        self.used = True
        with httpx.Client(timeout=15, follow_redirects=False, trust_env=False, transport=transport) as client:
            with client.stream("POST", "https://oauth2.googleapis.com/token", data={
                "grant_type": "authorization_code", "client_id": self.client_id, "client_secret": self.client_secret,
                "code": code, "code_verifier": self.verifier, "redirect_uri": self.redirect,
            }) as response:
                token = bounded_json(response)
            scopes = set(token.get("scope", "").split())
            if SEND_SCOPE not in scopes or scopes - ALLOWED_SCOPES or not token.get("refresh_token") or not token.get("access_token"):
                raise ValueError("send_only_offline_consent_required")
            self.refresh_expires_in = token.get("refresh_token_expires_in")
            with client.stream("GET", "https://openidconnect.googleapis.com/v1/userinfo",
                               headers={"Authorization": "Bearer " + token["access_token"]}) as response:
                identity = bounded_json(response)
            if identity.get("email", "").casefold() != self.sender or identity.get("email_verified") is not True:
                raise ValueError("wrong_google_account")
        values = {"GMAIL_MAIL_ENABLED": "true", "GMAIL_MAIL_CLIENT_ID": self.client_id,
                  "GMAIL_MAIL_CLIENT_SECRET": self.client_secret, "GMAIL_MAIL_REFRESH_TOKEN": token["refresh_token"],
                  "GMAIL_MAIL_SENDER": self.sender, "SMTP_ENABLED": "false", "RESEND_ENABLED": "false", "LOCAL_MAIL_ENABLED": "false"}
        if any(not isinstance(value, str) or "\n" in value or "\r" in value for value in values.values()):
            raise ValueError("invalid_token_format")
        return values


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Callback URLs contain a short-lived authorization code.

    def page(self, title, detail, *, status=200):
        body = f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TalentSync · Correo</title>
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#090d16;color:#e0f2fe;font:16px/1.7 Arial,sans-serif}}main{{margin:20px;max-width:500px;padding:36px;border:1px solid #2b3a4f;border-top:4px solid #38bdf8;border-radius:20px;background:#111827}}small{{color:#38bdf8;font-weight:bold;letter-spacing:2px}}h1{{line-height:1.2}}p{{color:#a8b3c5}}</style>
<main><small>TALENTSYNC · CORREO</small><h1>{escape(title)}</h1><p>{escape(detail)}</p></main></html>'''.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            self.page("Solicitud no válida", "Usa la dirección de configuración de este equipo.", status=400)
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/start" and not parsed.query and not self.server.auth.used:
            self.send_response(302)
            self.send_header("Location", self.server.auth.url())
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
        elif parsed.path == "/callback":
            query = parse_qs(parsed.query, max_num_fields=12)
            if (self.server.auth.used or len(query.get("state", [])) != 1 or len(query.get("code", [])) != 1
                    or not hmac.compare_digest(query["state"][0], self.server.auth.state)):
                self.page("No se completó la conexión", "No se recibió una autorización válida. Puedes cerrar esta pestaña.", status=400)
                return
            try:
                values = self.server.auth.complete(query["code"][0], query["state"][0])
                private_write(self.server.output, "# Private send-only project Gmail authorization. Never commit.\n" + "\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
                self.server.result = "authorized"
            except (httpx.HTTPError, ValueError, TypeError, OSError, AttributeError) as failure:
                self.server.result = "failed"
                self.server.failure_type = type(failure).__name__
            self.send_response(303)
            self.send_header("Location", "/complete")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
        elif parsed.path == "/complete":
            if self.server.result == "authorized":
                self.page("Correo conectado", f"La autorización de envío de {self.server.auth.sender} se guardó de forma privada. TalentSync no tiene permiso para leer tu buzón. Ahora comprobaremos el envío.")
            else:
                self.page("No se completó la conexión", "No se guardó una autorización válida. Revisa la cuenta seleccionada y los permisos concedidos.", status=400)
        else:
            self.page("TalentSync · Configuración", "Esta dirección solo se utiliza para conectar el correo de la plataforma.", status=404)


def main():
    parser = argparse.ArgumentParser(description="Autorizar el Gmail del proyecto con permiso de solo envío")
    parser.add_argument("--client-file", type=Path, default=ROOT / ".local/gmail-oauth-client.json")
    parser.add_argument("--sender", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / ".local/gmail-production.env")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / ".local").resolve()) or output.exists():
        raise SystemExit("Usa un archivo privado nuevo dentro de .local; no se sobrescriben autorizaciones.")
    try:
        credentials = json.loads(args.client_file.read_text(encoding="utf-8-sig"))
        with HTTPServer(("127.0.0.1", 0), Handler) as server:
            server.auth = Authorization(credentials, args.sender, f"http://127.0.0.1:{server.server_port}/callback")
            server.output, server.result, server.failure_type = output, "pending", None
            server.timeout = 1
            start = f"http://127.0.0.1:{server.server_port}/start"
            (ROOT / ".local/gmail-authorization-request.json").write_text(json.dumps({"start_url": start, "sender": server.auth.sender, "scopes": SCOPES}), encoding="utf-8")
            print(json.dumps({"status": "waiting_for_google_consent", "start_url": start, "sender": server.auth.sender}), flush=True)
            deadline = time.monotonic() + 1800
            completed = None
            while time.monotonic() < deadline:
                server.handle_request()
                if server.result != "pending":
                    completed = completed or time.monotonic()
                    if time.monotonic() - completed > 90:
                        break
            report = {"status": server.result, "sender": server.auth.sender, "failure_type": server.failure_type,
                      "inbox_read_permission": False, "test_email_sent": False,
                      "refresh_expires_in": server.auth.refresh_expires_in}
            (ROOT / ".local/gmail-authorization-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report), flush=True)
            return 0 if server.result == "authorized" else 1
    except (httpx.HTTPError, ValueError, TypeError, OSError, AttributeError) as failure:
        print(json.dumps({"status": "setup_failed", "error": type(failure).__name__}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
