from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_unit_of_work, require_roles
from app.application.errors import UseCaseError
from app.application.use_cases import delivery_events
from app.core.config import settings
from app.core.limiter import limiter
from app.domain.entities.enums import UserRole
from app.domain.services.mail_webhooks import verify_event

router = APIRouter()


@router.post("/webhooks/resend")
@limiter.limit("300/minute")
async def resend_event(request: Request, db=Depends(get_unit_of_work)):
    if not settings.resend_webhook_secret:
        raise UseCaseError(status_code=404, detail="No encontrado")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 65536:
            raise UseCaseError(status_code=413, detail="Evento demasiado grande")
    try:
        event = verify_event(bytes(body), request.headers, settings.resend_webhook_secret)
    except ValueError:
        raise UseCaseError(status_code=400, detail="Firma o evento de correo inválido") from None
    if event:
        delivery_events.record(db, event, settings.mail_event_retention_days)
    return {"received": True}


@router.get("/admin/mail-delivery")
def delivery_status(page: int = Query(default=1, ge=1), user=Depends(require_roles(UserRole.ADMIN)), db=Depends(get_unit_of_work)):
    total, rows = db.accounts.mail_status_page((page - 1) * 20, 20)
    return {"page": page, "page_size": 20, "total": total, "items": [{"id": row.id, "queue_state": row.delivery_state, "transport_status": row.transport_status, "attempts": row.attempts, "created_at": row.created_at, "accepted_at": row.sent_at, "event_at": row.provider_event_at, "failure_kind": row.failure_kind} for row in rows],
            "note": "Aceptado por el transporte no significa entregado. SMTP y Gmail sin eventos de entrega no confirman recepción ni lectura."}
