import io
import json
import secrets
import zipfile
from datetime import datetime, timedelta
from enum import Enum

from app.application.errors import UseCaseError
from app.application.use_cases.account_security import _mfa, _password

MAX_EXPORT = 50 * 1024 * 1024


def authorize(db, user, payload, security):
    _password(user, payload["password"], security)
    _mfa(db, user, payload.get("code"), security)


def status(db, user):
    return {"deletion_block": db.account_data.deletion_block(user), "export_format": "ZIP: datos JSON, PDF guardados y archivos originales disponibles",
            "note": "La eliminación retira tu perfil, postulaciones, CV, prácticas y sesiones. Las copias descargadas por otras personas y las copias de seguridad tienen su propio ciclo de conservación."}


def serialize(value):
    if isinstance(value, datetime):
        return value.isoformat() + "Z"
    if isinstance(value, Enum):
        return value.value
    raise TypeError("Unsupported export value")


def export(db, user, payload, security, files):
    authorize(db, user, payload, security)
    try:
        document, pdfs = db.account_data.export(user)
    except ValueError:
        raise UseCaseError(status_code=413, detail="La copia supera 50 MB. Contacta con soporte para una exportación asistida.") from None
    document["manifest"] = {"schema": 1, "generated_at": datetime.utcnow().isoformat() + "Z", "scope": "Datos propios; sin credenciales ni notas privadas de empresas", "files": []}
    try:
        owned = files.export(user.id)
    except Exception:
        raise UseCaseError(status_code=503, detail="No pudimos reunir los archivos privados. La exportación no se ha descargado; vuelve a intentarlo o contacta con soporte.") from None
    entries = [(f"cv/{identifier}.pdf", pdf) for identifier, pdf in pdfs] + owned
    document["manifest"]["files"] = [name for name, _ in entries]
    document["manifest"]["original_cv_available"] = any(".pdf" in name.lower() for name, _ in owned)
    raw = json.dumps(document, ensure_ascii=False, default=serialize, indent=2).encode()
    if len(raw) + sum(len(content) for _, content in entries) > MAX_EXPORT:
        raise UseCaseError(status_code=413, detail="La copia supera 50 MB. Contacta con soporte para una exportación asistida.")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("datos.json", raw)
        for name, content in entries:
            archive.writestr(name, content)
    db.commit()  # persist consumed one-time MFA/recovery code
    return output.getvalue()


def process_erasure(db, task, files):
    lease = secrets.token_urlsafe(24)
    if not db.account_data.claim_erasure(task.id, lease, datetime.utcnow()):
        db.refresh(task)
        return task.state == "completed"
    db.commit()
    db.refresh(task)
    try:
        files.erase(task.owner_id)
        values = {"state": "completed", "owner_id": None, "completed_at": datetime.utcnow(), "next_attempt_at": None}
    except Exception:
        attempts = task.attempts + 1
        values = {"state": "retry", "attempts": attempts, "next_attempt_at": datetime.utcnow() + timedelta(minutes=min(2 ** min(attempts, 10), 1440))}
    db.account_data.finish_erasure(task.id, lease, values)
    db.commit()
    db.refresh(task)
    return task.state == "completed"


def erase(db, user, payload, security, files):
    if payload.get("confirmation") != "ELIMINAR":
        raise UseCaseError(status_code=422, detail="Escribe ELIMINAR para confirmar")
    authorize(db, user, payload, security)
    db.account_data.lock_deletion(user)
    block = db.account_data.deletion_block(user)
    if block:
        raise UseCaseError(status_code=409, detail=block)
    task = db.account_data.erasure_task(user.id)
    db.personalization.purge_user(user.id)
    db.account_data.erase(user)
    db.commit()  # durable removal first; file failures remain retryable
    completed = process_erasure(db, task, files)
    return {"receipt": task.id, "files_pending": not completed, "message": "Cuenta eliminada. Archivos privados eliminados." if completed else "Cuenta eliminada. La limpieza de archivos privados está pendiente y se volverá a intentar."}
