"""Capabilities, configuration and observed results are separate facts."""
from datetime import datetime, timedelta

from app.domain.services.market_radar import MINIMUM_SAMPLE


def integration_readiness(*, neural_active, local_mail, smtp, providers, catalog, resend=False, learn=False, github_projects=False, codewars=False, youtube=False, public_learning=False, observations=None, now=None, catalog_providers=None):
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
                    if now - datetime.fromisoformat(success.rstrip("Z")) > timedelta(hours=24):
                        operational = "stale"
                except (ValueError, TypeError):
                    operational = "unverified"
        row = {"id": key, "name": name, "state": state, "status": status, "next_steps": next_steps,
               "implemented": True, "enabled": enabled, "configured": configured, "operational_state": operational,
               "last_success_at": success, "last_attempt_at": seen.get("last_attempt_at"), "last_error": error if enabled and configured is not False else ""}
        if action_url:
            row.update(action_url=action_url, action_label=action_label)
        rows.append(row)

    add("matching", "Modelo de compatibilidad", "local_ready" if neural_active else "local_fallback", "Modelo neuronal activo en este proceso." if neural_active else "Compatibilidad léxica disponible como alternativa local.", "Revisar afinidad y brechas con los escenarios de candidato.")
    add("mail", "Correo y avisos", "local_ready" if local_mail else "configured" if smtp or resend else "disabled", "Bandeja de desarrollo; no entrega correo externo." if local_mail else "Transporte externo configurado; la aceptación no confirma entrega al destinatario." if smtp or resend else "No hay transporte habilitado.", "Revisar la bandeja local." if local_mail else "Comprobar envío, entrega y rebotes con una cuenta autorizada.", configured=True if local_mail else bool(smtp or resend), enabled=bool(local_mail or smtp or resend))
    for key, title, names in [("social", "Acceso social", ("google", "github", "linkedin")), ("sso", "SSO administrativo", ("workspace", "entra"))]:
        active = [name for name in names if providers.get(name)]
        add(key, title, "configured" if active else "provider_required", "Proveedores configurados: " + (", ".join(active) or "ninguno") + ".", "Comprobar acceso, vinculación y recuperación con una cuenta autorizada.", configured=bool(active))
    sources = catalog_providers if catalog_providers is not None else {"jsearch": bool(catalog)}
    for key, configured in sources.items():
        if key != "jsearch" and not configured:
            continue
        name = {"jsearch": "JSearch", "jooble": "Jooble", "adzuna": "Adzuna"}[key]
        add(key, "Vacantes externas · " + name, "configured" if configured else "local_manual", "Fuente configurada. La importación manual CSV/Excel también está disponible." if configured else "Importación manual CSV/Excel disponible; sin fuente automática configurada.", "Revisar vigencia, duplicados y el resultado de la sincronización.", configured=bool(configured), action_url="/vacantes", action_label="Revisar vacantes")
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
