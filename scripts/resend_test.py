"""One authorized Resend smoke test. Never imports the database or drains mail."""
import json
import secrets
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from pydantic import EmailStr, TypeAdapter, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.application.ports.services import MailDeliveryError
from app.infrastructure.security.resend import ResendDelivery

SUBJECT = "TalentSync — prueba de conexión de correo"
BODY = (
    "Hola, José.\n\n"
    "Esta es la prueba de conexión de TalentSync con Resend que solicitaste.\n"
    "El envío de prueba está limitado a esta dirección. Las cuentas ficticias "
    "de la demostración siguen utilizando la bandeja local.\n\n"
    "No necesitas realizar ninguna acción ni compartir contraseñas.\n\nTalentSync"
)


def load_config(path):
    # No inherited shell settings, backend/.env, dotenv expansion or database.
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key in values:
            raise ValueError("Configuración de prueba inválida.")
        values[key] = value.strip()
    key = values.get("RESEND_API_KEY", "")
    if values.get("RESEND_TEST_ENABLED") != "true" or not key.startswith("re_") or any(c.isspace() for c in key):
        raise ValueError("Configura la clave privada y habilita la prueba local.")
    if values.get("RESEND_FROM") != "onboarding@resend.dev":
        raise ValueError("Esta prueba requiere el remitente de pruebas de Resend.")
    try:
        recipient = str(TypeAdapter(EmailStr).validate_python(values.get("RESEND_TEST_RECIPIENT", "")))
    except ValidationError:
        raise ValueError("Configura una única dirección autorizada de Resend.") from None
    return SimpleNamespace(resend_enabled=True, resend_api_key=key,
                           resend_from=values["RESEND_FROM"], recipient=recipient)


def save_state(path, state):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
    temporary.replace(path)


def run_test(config_path, state_path, *, transport=None, now=None):
    config = load_config(config_path)
    timestamp = time.time() if now is None else now
    state_path.parent.mkdir(parents=True, exist_ok=True)
    # One local command at a time; provider idempotency also protects retries.
    lock = state_path.with_suffix(".lock")
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError:
        raise ValueError("Ya hay una prueba de correo en curso.") from None
    try:
        handle.close()
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state["recipient"] != config.recipient or state["sender"] != config.resend_from:
                raise ValueError("La prueba guardada pertenece a otra configuración.")
            if state["status"] == "accepted":
                return "already_accepted"
            if not 0 <= timestamp - state["created_at"] < 23 * 3600:
                raise ValueError("Prueba antigua: revisa el panel de Resend antes de repetir el envío.")
        else:
            state = {"recipient": config.recipient, "sender": config.resend_from,
                     "secret": secrets.token_urlsafe(48), "created_at": timestamp,
                     "status": "pending"}
            save_state(state_path, state)
        config.secret_key = state["secret"]
        try:
            ResendDelivery(config, transport).send(recipient=config.recipient,
                subject=SUBJECT, body=BODY, message_id=1)
        except MailDeliveryError as error:
            state.update(status="uncertain", failure_kind=error.kind)
            save_state(state_path, state)
            raise
        state.update(status="accepted", accepted_at=timestamp)
        state.pop("failure_kind", None)
        save_state(state_path, state)
        return "accepted"
    finally:
        lock.unlink(missing_ok=True)


def main():
    try:
        result = run_test(ROOT / ".local/resend.env", ROOT / ".local/verification/resend-test.json")
    except MailDeliveryError as error:
        raise SystemExit(f"Resend no confirmó la aceptación del correo ({error.kind}). No se procesó la bandeja local.") from None
    except (ValueError, KeyError, TypeError, OSError):
        raise SystemExit("No se pudo completar la prueba. Revisa la configuración privada y el estado guardado; no se muestran secretos.") from None
    print("Correo de prueba aceptado por Resend." if result == "accepted"
          else "La prueba ya fue aceptada anteriormente; no se envió otro correo.")


if __name__ == "__main__":
    main()
