import { useId, useState } from "react";
import { CalendarDays, ChevronDown, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";

const labels = { none: "Sin sincronizar", pending: "Sincronización pendiente", synced: "Entrevista sincronizada", needs_sync: "Actualización pendiente", retry: "Se volverá a intentar", failed: "Necesita revisión", cancelled: "Evento cancelado" };

export function CalendarSync({ applicationId }) {
  const panelId = useId();
  const [open, setOpen] = useState(false), [connection, setConnection] = useState(null), [event, setEvent] = useState(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [minutes, setMinutes] = useState(45);
  async function show() {
    if (open) { setOpen(false); return; }
    setOpen(true); setBusy(true); setError("");
    try { const [a, b] = await Promise.all([api.get("/account/calendar"), api.get(`/workflow/applications/${applicationId}/calendar`)]); setConnection(a.data); setEvent(b.data); setMinutes(b.data.minutes); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  async function sync() {
    setBusy(true); setError("");
    try { const { data } = await api.post(`/workflow/applications/${applicationId}/calendar`, { minutes: Number(minutes) }, { __quiet: true }); setEvent(data); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <div className="calendar-sync"><button type="button" className="button-secondary button-sm calendar-sync-trigger" aria-expanded={open} aria-controls={panelId} onClick={show}><CalendarDays size={16} /><span>Google Calendar</span><ChevronDown size={14} className="calendar-sync-caret" aria-hidden="true" /></button>{open && <div id={panelId} className="calendar-sync-options">{busy && <p role="status">Actualizando calendario…</p>}{error && <p role="alert">{error}</p>}{connection && (!connection.connected || !connection.configured ? <p>Conecta tu calendario desde <Link to="/seguridad#security-calendar">Seguridad de cuenta</Link>.</p> : <><p role="status">{labels[event?.state] || "Consulta la sincronización"}</p>{event?.error && <p role="alert">{event.error}</p>}<label>Duración de la copia<select className="field-control" value={minutes} disabled={busy} onChange={(e) => setMinutes(e.target.value)}>{[15, 30, 45, 60, 90, 120, 180].map((value) => <option key={value} value={value}>{value} minutos</option>)}</select></label><small>Confirma la duración con la empresa. Se copia en tu calendario sin añadir invitados.</small><button type="button" className="button-primary button-sm" disabled={busy} onClick={sync}><RefreshCw size={15} />{event?.enabled ? "Actualizar entrevista" : "Sincronizar entrevista"}</button></>)}</div>}</div>;
}
