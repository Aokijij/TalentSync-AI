"""Server-owned evidence of an explicit, versioned registration decision."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.application.errors import UseCaseError

DOCUMENTS = json.loads((Path(__file__).resolve().parents[3] / "legal_documents/current.json").read_text(encoding="utf-8"))


def registration_consent(payload, *, channel):
    if payload.get("data_processing_accepted") is not True or payload.get("terms_accepted") is not True:
        raise UseCaseError(status_code=422, detail="Debes autorizar el tratamiento de datos y aceptar los términos para crear tu cuenta")
    for field in ("privacy_version", "terms_version"):
        if payload.get(field) != DOCUMENTS[field]:
            raise UseCaseError(status_code=422, detail="Los documentos legales se actualizaron. Recarga el registro y revisa su versión vigente")
    notice = DOCUMENTS["data_processing_notice"] + "\n" + DOCUMENTS["terms_notice"]
    return {
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "privacy_version": DOCUMENTS["privacy_version"], "terms_version": DOCUMENTS["terms_version"],
        "data_processing_accepted": True, "terms_accepted": True,
        "channel": channel, "notice": notice,
        "notice_sha256": hashlib.sha256(notice.encode()).hexdigest(),
    }
