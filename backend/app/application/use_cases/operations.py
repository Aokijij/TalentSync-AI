def readiness(db, storage):
    checks = {}
    try:
        db.ping()
        checks["database"] = True
    except Exception:
        checks["database"] = False
    try:
        checks["private_storage"] = bool(storage.storage_available())
    except Exception:
        checks["private_storage"] = False
    return {"status": "ready" if all(checks.values()) else "not_ready", "checks": checks}


def status(db, storage, metrics, *, calendar_configured, retention_enabled, cleanup_enabled=True):
    result = readiness(db, storage)
    result["requests"] = metrics.snapshot()
    result["queues"] = db.account_data.queue_counts()
    result["calendar_configured"] = calendar_configured
    result["retention_enabled"] = retention_enabled and cleanup_enabled
    result["cleanup_enabled"] = cleanup_enabled
    alerts = []
    if result["status"] != "ready":
        alerts.append("Una dependencia necesaria no está disponible.")
    for key, label in (("mail_failed", "Hay correos que agotaron los reintentos."), ("calendar_failed", "Hay entrevistas pendientes de volver a autorizar o sincronizar."), ("file_erasure_pending", "Hay archivos privados pendientes de limpieza.")):
        if result["queues"][key]:
            alerts.append(label)
    if not cleanup_enabled:
        alerts.append("Los reintentos de limpieza de archivos están desactivados.")
    if not retention_enabled or not cleanup_enabled:
        alerts.append("La conservación automática de datos vencidos está desactivada.")
    if any(row["samples"] >= 20 and (row["p95_ms"] > 2000 or row["errors"] / row["samples"] > .05) for row in result["requests"]["routes"]):
        alerts.append("Una ruta supera 2 s en p95 o 5 % de errores con al menos 20 muestras.")
    result["alerts"] = alerts
    result["note"] = "Muestras de este proceso, últimos 15 minutos; no representan todos los servidores. Revisar con monitorización externa antes de publicar."
    return result
