import { CalendarSync } from "./CalendarSync.jsx";
import "../styles/account-controls.css";
import { useState } from "react";
import { ArrowUpRight, CalendarClock, Download, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { saveBlob } from "../utils/preparation.js";
import { activeInterview, interviewDateParts, upcomingInterviews } from "../utils/interviewAgenda.js";
import "../styles/interview-agenda.css";

export function InterviewCalendarButton({ applicationId }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [saved, setSaved] = useState(false);
  async function download() {
    if (busy) return;
    setBusy(true); setError(""); setSaved(false);
    try {
      const { data } = await api.get(`/workflow/applications/${applicationId}/interview.ics`, { responseType: "blob", __quiet: true });
      saveBlob(data, `Entrevista TalentSync ${applicationId}.ics`); setSaved(true);
    } catch (failure) {
      try { if (failure.response?.data instanceof Blob) failure.response.data = JSON.parse(await failure.response.data.text()); } catch { /* Non-JSON errors use the fallback. */ }
      setError(getApiErrorMessage(failure, "No pudimos descargar la cita. Vuelve a intentarlo."));
    } finally { setBusy(false); }
  }
  return <div className="interview-calendar-actions" role="group" aria-label="Calendario de la entrevista"><CalendarSync applicationId={applicationId} /><button type="button" className="button-secondary button-sm interview-calendar-download" disabled={busy} onClick={download}>{busy ? <RefreshCw size={16} className="animate-spin" /> : <Download size={16} />}{busy ? "Preparando…" : "Descargar cita"}</button>{error && <p role="alert">{error}</p>}{saved && <p role="status">Archivo descargado. Ábrelo en tu calendario para guardar la cita.</p>}</div>;
}

export function InterviewAgenda({ applications, loading = false, error = "", now = new Date() }) {
  const [expanded, setExpanded] = useState(false);
  const upcoming = upcomingInterviews(applications, now);
  const visible = expanded ? upcoming : upcoming.slice(0, 3);
  return <section className="interview-agenda ui-panel" aria-label="Agenda de entrevistas"><header className="ui-panel-heading"><div className="interview-agenda-heading"><span><CalendarClock size={22} /></span><div><h2>Tu agenda de entrevistas</h2><p>{loading ? "Consultando las citas de tus procesos…" : error ? "La agenda no está disponible." : upcoming.length ? `${upcoming.length} ${upcoming.length === 1 ? "cita próxima" : "citas próximas"} · Hora de Colombia` : "Las próximas citas aparecerán aquí cuando la empresa las programe."}</p></div></div></header>
    {error ? <p role="alert" className="interview-agenda-note">{error}</p> : loading ? <p role="status" className="interview-agenda-note">Cargando entrevistas…</p> : !!upcoming.length && <><ol className="interview-agenda-list">{visible.map((row) => <InterviewRow key={row.id} row={row} />)}</ol>{upcoming.length > 3 && <div className="interview-agenda-more"><button type="button" className="button-secondary button-sm" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? "Mostrar solo las próximas 3" : `Ver las ${upcoming.length} entrevistas`}</button></div>}<CalendarNote /></>}
  </section>;
}

export function ProcessInterview({ process, now = new Date() }) {
  if (!process.interview_at) return null;
  const parts = interviewDateParts(process.interview_at);
  if (!parts) return null;
  const upcoming = activeInterview(process, now);
  return <section className="interview-process ui-panel"><div className="interview-process-content"><div className="interview-date-tile" aria-hidden="true"><strong>{parts.day}</strong><span>{parts.month}</span></div><div><h2>{upcoming ? "Tu próxima entrevista" : "Última entrevista programada"}</h2><p>{parts.full} · <strong>{parts.time}</strong></p><small>Hora de Colombia (UTC−5) · Duración por confirmar</small></div>{upcoming && <InterviewCalendarButton applicationId={process.application_id} />}</div>{upcoming ? <CalendarNote /> : <p className="interview-agenda-note">{process.released_at || ["rejected", "accepted", "hired"].includes(process.status) ? "El proceso finalizó. Esta fecha se conserva como referencia." : "La fecha ya pasó. Consulta con la empresa si hay una nueva cita."}</p>}</section>;
}

function InterviewRow({ row }) {
  const parts = interviewDateParts(row.interview_at);
  return <li><div className="interview-date-tile" aria-hidden="true"><strong>{parts.day}</strong><span>{parts.month}</span></div><div className="interview-agenda-info"><span>{row.company_name || "Empresa"}</span><h3>{row.job_title || "Proceso de selección"}</h3><p>{parts.full} · <strong>{parts.time}</strong></p><Link to={`/procesos/${row.id}`}>Ver proceso<ArrowUpRight size={14} /></Link></div><InterviewCalendarButton applicationId={row.id} /></li>;
}

function CalendarNote() {
  return <p className="interview-agenda-note">El archivo descargado es una copia sin actualizaciones. Con Google Calendar puedes sincronizar los cambios de la entrevista. Ambas opciones incluyen un recordatorio de 30 minutos. Confirma la duración y el acceso con la empresa.</p>;
}
