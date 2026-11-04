"""Capabilities, configuration and observed results are separate facts."""
from datetime import datetime, timedelta, timezone

from app.domain.services.market_radar import MINIMUM_SAMPLE


def integration_readiness(*, neural_active, local_mail, smtp, providers, catalog, resend=False, gmail=False, learn=False, github_projects=False, codewars=False, youtube=False, public_learning=False, observations=None, now=None, catalog_providers=None, calendar=False, mail_events=False, health_reports=None, writing_service=None):
    now = now or datetime.utcnow()
    observations = observations or {}
    rows = []

    def add(key, name, state, status, next_steps, *, configured=None, enabled=True, action_url=None, action_label=None):
        seen = observations.get(key, {})
        success = seen.get("last_success_at")
        error = seen.get("last_error", "")
        operational = "disabled" if not enabled else "not_configured" if configured is False else "manual" if state == "local_manual" else "local" if state in {"local_ready", "local_fallback"} else "unverified"
        if enabled and configured is not False and seen.get("last_attempt_at"):
            operational = "error" if error else "observed"
            if not error and success:
                try:
                    recorded = datetime.fromisoformat(success.replace("Z", "+00:00"))
                    recorded = recorded.astimezone(timezone.utc).replace(tzinfo=None) if recorded.tzinfo else recorded
                    reference = now.astimezone(timezone.utc).replace(tzinfo=None) if now.tzinfo else now
                    if reference - recorded > timedelta(hours=24):
                        operational = "stale"
                except (ValueError, TypeError):
                    operational = "unverified"
        row = {"id": key, "name": name, "state": state, "status": status, "next_steps": next_steps,
               "implemented": True, "enabled": enabled, "configured": configured, "operational_state": operational,
               "last_success_at": success, "last_attempt_at": seen.get("last_attempt_at"), "operation": seen.get("operation", ""), "last_error": error if enabled and configured is not False else ""}
        health = (health_reports or {}).get(key)
        if health:
            row["automatic_check"] = health
            try:
                checked = datetime.fromisoformat(health["checked_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                fresh = (now.replace(tzinfo=None) - checked) < timedelta(hours=24)
            except (ValueError, TypeError, KeyError):
                fresh = False
            if fresh and enabled and configured is not False:
                row["operational_state"] = "reachable" if health["state"] == "available" else "error"
        if action_url:
            row.update(action_url=action_url, action_label=action_label)
        rows.append(row)

    add("matching", "Modelo de compatibilidad", "local_ready" if neural_active else "local_fallback", "Modelo neuronal activo en este proceso." if neural_active else "Compatibilidad léxica disponible como alternativa local.", "Revisar afinidad y brechas con los escenarios de candidato.")
    if writing_service and writing_service.get("external"):
        available = writing_service["available"]
        add("career_writer", "Redacción asistida · Groq", "configured" if available else "provider_required", "Propuestas por solicitud del candidato, con autorización previa y límites de uso. La comprobación automática consulta los modelos disponibles; no envía textos ni consume generaciones.", "Revisar la configuración del servidor y las cuotas de la cuenta gratuita si la conexión no está disponible.", configured=available)
    add("mail", "Correo y avisos", "local_ready" if local_mail else "configured" if smtp or resend or gmail else "disabled", "Bandeja de desarrollo; no entrega correo externo." if local_mail else "Envío mediante Gmail autorizado; la aceptación no confirma entrega al destinatario." if gmail else "Transporte externo configurado; la aceptación no confirma entrega al destinatario." if smtp or resend else "No hay transporte habilitado.", "Revisar la bandeja local." if local_mail else "Comprobar envío, entrega y rebotes con una cuenta autorizada.", configured=True if local_mail else bool(smtp or resend or gmail), enabled=bool(local_mail or smtp or resend or gmail))
    add("calendar", "Google Calendar", "configured" if calendar else "provider_required", "Sincronización de entrevistas elegidas; cambios y cancelaciones con reintentos." if calendar else "Sincronización implementada; falta habilitar la aplicación de Google Calendar.", "Conectar desde Seguridad y añadir una entrevista desde la agenda. Comprobar sus detalles, cambios y cancelaciones.", configured=calendar, action_url="/seguridad#security-calendar", action_label="Revisar calendario")
    if resend:
        add("mail_events", "Confirmación de entrega de correo", "configured" if mail_events else "provider_required", "Eventos firmados de Resend: entrega, retrasos y rebotes." if mail_events else "El transporte puede aceptar mensajes, pero falta configurar el webhook firmado de entrega.", "Revisar los estados desde Operación y correos.", configured=mail_events)
    for key, title, names in [("social", "Acceso social", ("google", "github")), ("sso", "SSO administrativo", ("workspace", "entra"))]:
        active = [name for name in names if providers.get(name)]
        if active:
            for name in active:
                add(key + "_" + name, title + " · " + {"google": "Google", "github": "GitHub", "workspace": "Workspace", "entra": "Microsoft Entra"}[name], "configured", "Configuración disponible. Las fechas corresponden a un intercambio de identidad o acceso completado; no equivalen a aprobación pública del proveedor.", "Comprobar acceso y recuperación con una cuenta autorizada. La verificación de marca y permisos de Google se gestiona por separado.", configured=True)
        else:
            add(key, title, "provider_required", "Sin proveedor configurado. No es necesario para los métodos de acceso ya disponibles.", "Configurar solo si se necesita este método de acceso.", configured=False, enabled=key != "sso")
    sources = catalog_providers if catalog_providers is not None else {"jsearch": bool(catalog)}
    for key, configured in sources.items():
        if key != "jsearch" and not configured:
            continue
        name = {"jsearch": "JSearch", "jooble": "Jooble", "adzuna": "Adzuna", "greenhouse": "Greenhouse", "lever": "Lever", "ashby": "Ashby", "getonboard": "Get on Board"}[key]
        add(key, "Vacantes externas · " + name, "configured" if configured else "local_manual", "Fuente disponible para consulta editorial. Se comprueba la vigencia antes de recomendar." if configured else "Agregador opcional sin activar. Puedes consultar portales originales o importar un archivo autorizado desde Administración.", "Revisar vigencia, duplicados y el resultado de la sincronización.", configured=bool(configured), enabled=bool(configured), action_url="/administracion", action_label="Revisar vacantes")
    add("external_jobs", "Vigencia de vacantes externas", "configured", "Comprobación de la fuente original y vencimiento. Una respuesta HTTP correcta por sí sola no acredita que la oferta siga abierta.", "Revisar las ofertas sin confirmar desde Administración. Solo se recomiendan las comprobadas recientemente.", configured=True, action_url="/administracion", action_label="Revisar vacantes externas")
    for key, name, configured in [("youtube", "YouTube", youtube), ("microsoft_learn", "Microsoft Learn", learn)]:
        add(key, name, "configured" if configured else "provider_required", "Consulta e importación editorial disponibles; los recursos se revisan antes de publicar.", "Consultar la fuente desde el catálogo. Las fechas registran el resultado de esa operación y pueden incluir caché.", configured=configured, action_url="/admin/aprendizaje", action_label="Revisar fuente")
    for key, name in [("sena", "SENA"), ("sapiencia", "Sapiencia")]:
        add(key, name, "configured" if public_learning else "local_manual", "Consultas manuales disponibles. " + ("Actualización periódica habilitada." if public_learning else "Actualización periódica desactivada."), "Revisar disponibilidad, vigencia y última actualización del catálogo.", configured=True, action_url="/admin/aprendizaje", action_label="Revisar fuente")
    add("certificates", "Cursos y certificados", "local_manual", "Catálogo, planes y evidencias declaradas disponibles; no autentican certificados.", "La verificación automática requiere acceso autorizado al proveedor.", action_url="/admin/aprendizaje", action_label="Revisar catálogo")
    add("verification", "Verificación empresarial", "local_manual", "Solicitud y revisión manual de soportes; sin consulta a registros oficiales.", "Revisar los soportes de cada organización.", action_url="/admin/verificaciones", action_label="Revisar organizaciones")
    add("salary", "Referencia salarial", "local_ready", f"Radar por ciudad o todo el país. Cada grupo salarial requiere al menos {MINIMUM_SAMPLE} empresas con condiciones comparables.", "Elegir área, nivel y ubicación. Los datos disponibles no representan todo el mercado laboral.")
    add("quality", "Calidad de ofertas", "local_ready", "Misiones, revisión de condiciones y borradores editables disponibles.", "Revisar la calidad antes de publicar.")
    add("practice", "Evaluaciones prácticas", "local_ready", "Retos guiados disponibles; ejecución SQL restringida en el backend.", "Revisar entregas y evidencias. No se ejecuta código arbitrario de otros lenguajes.")
    # Supplemental capabilities only appear when actually enabled.
    if github_projects:
        add("github_projects", "Proyectos públicos de GitHub", "configured", "Consulta pública por solicitud del candidato.", "Un repositorio no acredita autoría ni dominio profesional.", configured=True)
    if codewars:
        add("codewars", "Codewars", "configured", "Consulta pública por solicitud del candidato.", "Los rangos no certifican dominio ni titularidad.", configured=True)
    return rows
