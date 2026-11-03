import { useEffect, useId, useState } from "react";
import { CalendarDays, CheckCircle2, ChevronDown, ExternalLink, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";

const labels = { none: "Aún no está en tu calendario", pending: "Guardando en Google Calendar…", synced: "Entrevista sincronizada", needs_sync: "Actualizando los cambios…", retry: "Google no respondió. Volveremos a intentarlo", failed: "La sincronización necesita atención", cancelled: "Evento cancelado" };

export function CalendarSync({ applicationId }) {
  const panelId = useId();
  const [open, setOpen] = useState(false), [connection, setConnection] = useState(null), [event, setEvent] = useState(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    api.get(`/workflow/applications/${applicationId}/calendar`, { signal: controller.signal, __quiet: true }).then(({ data }) => { if (!controller.signal.aborted) setEvent(data); }).catch(() => {});
    return () => controller.abort();
  }, [applicationId]);
  useEffect(() => {
    if (!open || !["pending", "needs_sync", "retry"].includes(event?.state)) return;
    const timer = setTimeout(() => { api.get(`/workflow/applications/${applicationId}/calendar`, { __quiet: true }).then(({ data }) => setEvent(data)).catch((failure) => setError(getApiErrorMessage(failure))); }, 5000);
    return () => clearTimeout(timer);
  }, [open, event, applicationId]);
  async function show() {
    if (open) { setOpen(false); return; }
    setOpen(true); setBusy(true); setError("");
    try { const [a, b] = await Promise.all([api.get("/account/calendar", { __quiet: true }), api.get(`/workflow/applications/${applicationId}/calendar`, { __quiet: true })]); setConnection(a.data); setEvent(b.data); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  async function sync() {
    setBusy(true); setError("");
    try { const { data } = await api.post(`/workflow/applications/${applicationId}/calendar`, { minutes: event?.minutes || 45 }, { __quiet: true }); setEvent(data); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  const synced = event?.state === "synced";
  return <div className={`calendar-sync ${synced ? "is-synced" : ""}`}><button type="button" className="button-secondary button-sm calendar-sync-trigger" aria-expanded={open} aria-controls={open ? panelId : undefined} onClick={show}>{synced ? <CheckCircle2 size={16} /> : <CalendarDays size={16} />}<span>{synced ? "En Google Calendar" : "Añadir a Google Calendar"}</span><ChevronDown size={14} className="calendar-sync-caret" aria-hidden="true" /></button>{open && <div id={panelId} className="calendar-sync-options">{busy && <p role="status">Consultando Google Calendar…</p>}{error && <p role="alert">{error}</p>}{connection && (!connection.connected || !connection.configured || connection.needs_reconnect ? <><strong><CalendarDays size={20} />{connection.needs_reconnect ? "Renueva la conexión con Google" : "Conecta tu calendario"}</strong><p>Vincula tu cuenta desde Correo y acceso. Después vuelve al proceso y añade esta entrevista; sus cambios se mantendrán al día.</p><Link className="button-primary button-sm" to="/seguridad#security-calendar">{connection.needs_reconnect ? "Revisar conexión" : "Conectar Google Calendar"}</Link></> : <><strong role="status">{labels[event?.state] || "Consulta la sincronización"}</strong>{event?.error && <p role="alert">{event.error}</p>}<p>Incluye fecha, duración, modalidad y enlace o dirección. Si la empresa cambia o cancela la entrevista, el evento se actualizará automáticamente.</p><small>Recordatorio: 30 minutos antes. No se envían invitaciones a otras personas.</small><div className="calendar-sync-buttons">{!synced && <button type="button" className="button-primary button-sm" disabled={busy} onClick={sync}><RefreshCw size={15} />{event?.enabled ? "Reintentar sincronización" : "Añadir entrevista"}</button>}{synced && <a href="https://calendar.google.com/calendar/u/0/r" target="_blank" rel="noopener noreferrer" className="button-secondary button-sm">Abrir Google Calendar<ExternalLink size={14} /></a>}</div></>)}</div>}</div>;
}
