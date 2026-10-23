import { interviewState } from "../utils/recruitmentState.js";
import { CalendarSync } from "./CalendarSync.jsx";
import "../styles/account-controls.css";
import { useId, useState } from "react";
import { ArrowUpRight, CalendarClock, ChevronDown, Search, SlidersHorizontal } from "lucide-react";
import { Link } from "react-router-dom";
import { InterviewDetails } from "./InterviewDetails.jsx";
import { activeInterview, candidateInterviewGroup, candidateInterviewRows, interviewDateParts } from "../utils/interviewAgenda.js";
import "../styles/interview-agenda.css";
import "../styles/candidate-processes.css";
import { Pagination } from "./Pagination.jsx";
import { pageItems, paginationState } from "../utils/pagination.js";

export function InterviewCalendarButton({ applicationId }) {
  return <div className="interview-calendar-actions"><CalendarSync applicationId={applicationId} /></div>;
}

export function InterviewAgenda({ applications, loading = false, error = "", now = new Date(), active = true, onRetry }) {
  const [group, setGroup] = useState("upcoming"), [mode, setMode] = useState("all"), [search, setSearch] = useState("");
  const [page, setPage] = useState(1), [selected, setSelected] = useState(null);
  const rows = candidateInterviewRows(applications, { group, mode, search, now });
  const counts = { upcoming: 0, pending: 0, history: 0 };
  applications.forEach((row) => { const key = candidateInterviewGroup(row, now); if (key) counts[key]++; });
  const paging = paginationState(rows.length, page, 6);
  function filter(setter, value) { setter(value); setPage(1); setSelected(null); }
  return <section className="interview-agenda candidate-agenda ui-panel" aria-label="Agenda de entrevistas">
    <header className="ui-panel-heading"><div className="interview-agenda-heading"><span><CalendarClock size={22} /></span><div><h2>Tu agenda de entrevistas</h2><p>{loading ? "Consultando las citas de tus procesos…" : error ? "La agenda no está disponible." : `${counts.upcoming} ${counts.upcoming === 1 ? "cita próxima" : "citas próximas"} · Hora de Colombia`}</p></div></div><span className="candidate-agenda-timezone">UTC−5</span></header>
    {error ? <div role="alert" className="candidate-agenda-empty"><p>{error}</p>{onRetry && <button type="button" className="button-secondary" onClick={onRetry}>Reintentar</button>}</div> : loading ? <p role="status" className="candidate-agenda-empty">Cargando entrevistas…</p> : <>
      <div className="candidate-agenda-toolbar"><div className="candidate-agenda-groups" role="group" aria-label="Estado de las entrevistas">{[["upcoming", "Próximas"], ["pending", "Pendientes"], ["history", "Historial"]].map(([key, label]) => <button key={key} type="button" aria-pressed={key === group} onClick={() => filter(setGroup, key)}>{label}<span>{counts[key]}</span></button>)}</div>
      <div className="candidate-agenda-filters"><label className="candidate-agenda-search"><Search size={17} /><input type="search" aria-label="Buscar entrevista por empresa o vacante" placeholder="Buscar empresa o vacante" value={search} onChange={(event) => filter(setSearch, event.target.value)} /></label><label className="candidate-agenda-mode"><SlidersHorizontal size={16} /><select className="field-control" aria-label="Modalidad de la entrevista" value={mode} onChange={(event) => filter(setMode, event.target.value)}><option value="all">Todas las modalidades</option><option value="virtual">Virtual</option><option value="in_person">Presencial</option><option value="unknown">Por confirmar</option></select></label></div></div>
      <p className="candidate-agenda-context">{group === "upcoming" ? "Abre una cita para consultar el acceso y añadirla a Google Calendar." : group === "pending" ? "Consulta si la empresa ha confirmado la realización o está preparando su respuesta." : "Entrevistas anteriores y de procesos finalizados. Sus detalles se conservan para consulta."}</p>
      {rows.length ? <><ol className="candidate-interview-list">{pageItems(rows, paging.page, 6).map((row) => <InterviewRow key={`${row.id}-${row.version}`} row={row} group={group} active={active} expanded={selected === row.id} onToggle={() => setSelected((current) => current === row.id ? null : row.id)} />)}</ol><Pagination page={paging.page} pageSize={6} total={rows.length} label="Páginas de entrevistas" onChange={(value) => { setPage(value); setSelected(null); }} /></> : <div className="candidate-agenda-empty"><CalendarClock size={25} /><h3>{search || mode !== "all" ? "No hay citas con estos filtros" : group === "upcoming" ? "Sin entrevistas próximas" : group === "pending" ? "Sin entrevistas pendientes" : "Sin entrevistas en el historial"}</h3><p>{search || mode !== "all" ? "Prueba otra búsqueda o modalidad." : "Las citas aparecerán aquí cuando la empresa actualice el proceso."}</p>{(search || mode !== "all") && <button type="button" className="button-secondary button-sm" onClick={() => { setSearch(""); setMode("all"); setPage(1); setSelected(null); }}>Limpiar filtros</button>}</div>}
      {!!counts.upcoming && group === "upcoming" && <CalendarNote />}
    </>}
  </section>;
}

export function ProcessInterview({ process, now = new Date() }) {
  if (!process.interview_at) return null;
  const parts = interviewDateParts(process.interview_at);
  if (!parts) return null;
  const upcoming = activeInterview(process, now) && !process.interview_completed_at;
  const state = interviewState(process, now);
  return <section className="interview-process ui-panel"><div className="interview-process-content"><div className="interview-date-tile" aria-hidden="true"><strong>{parts.day}</strong><span>{parts.month}</span></div><div><h2>{upcoming ? "Tu próxima entrevista" : process.interview_completed_at ? "Entrevista realizada" : "Última entrevista programada"}</h2><p>{parts.full} · <strong>{parts.time}</strong></p><small>Hora de Colombia (UTC−5)</small><InterviewDetails details={process.interview_details} /></div>{upcoming && <InterviewCalendarButton key={process.version} applicationId={process.application_id} />}</div>{upcoming ? <CalendarNote /> : <p className="interview-agenda-note">{process.released_at || ["rejected", "accepted", "hired"].includes(process.status) ? "El proceso finalizó. Esta fecha se conserva como referencia." : state === "awaiting_response" ? "Entrevista realizada. La empresa está preparando su respuesta; consulta el plazo en el proceso." : "La fecha ya pasó. La empresa debe confirmar si la entrevista se realizó o si necesita reprogramarse."}</p>}</section>;
}

function InterviewRow({ row, group, expanded, onToggle, active }) {
  const panelId = useId(), parts = interviewDateParts(row.interview_at), mode = row.interview_details?.mode;
  const state = group === "upcoming" ? "Programada" : group === "pending" ? row.interview_completed_at ? "Esperando respuesta" : "Por confirmar realización" : row.released_at || ["rejected", "accepted", "hired"].includes(row.status) ? "Proceso finalizado" : "Entrevista anterior";
  return <li className={expanded ? "is-expanded" : ""}><button className="candidate-interview-summary" type="button" aria-expanded={expanded} aria-controls={expanded ? panelId : undefined} onClick={onToggle}>
    <span className="interview-date-tile" aria-hidden="true"><strong>{parts.day}</strong><span>{parts.month}</span></span>
    <span className="candidate-interview-identity"><span>{row.company_name || "Empresa"}</span><strong>{row.job_title || "Proceso de selección"}</strong><span className="candidate-interview-meta"><time dateTime={row.interview_at}><span className="candidate-interview-full-date">{parts.full}</span><span className="candidate-interview-short-date">{parts.short}</span><strong>{parts.time}</strong></time><span>· {mode === "virtual" ? "Virtual" : mode === "in_person" ? "Presencial" : "Modalidad por confirmar"}{row.interview_details?.minutes ? ` · ${row.interview_details.minutes} min` : ""}</span></span></span>
    <span className={`candidate-interview-status is-${group}`}>{state}</span><ChevronDown size={17} className="candidate-interview-caret" /></button>
    {expanded && <div id={panelId} className="candidate-interview-expanded"><div><h3>Acceso e indicaciones</h3><InterviewDetails details={row.interview_details} />{group === "pending" && <p className="candidate-interview-pending">{row.interview_completed_at ? "La empresa confirmó que se realizó la entrevista. Revisa el plazo de respuesta en tu proceso." : "La fecha ya pasó. La empresa debe confirmar si se realizó o necesita reprogramarse."}</p>}</div><div className="candidate-interview-actions"><Link className="button-secondary" to={`/procesos/${row.id}`}>Ver proceso<ArrowUpRight size={15} /></Link>{group === "upcoming" && active && <InterviewCalendarButton applicationId={row.id} />}</div></div>}
  </li>;
}

function CalendarNote() {
  return <p className="interview-agenda-note">Añade la entrevista a Google Calendar para ver su fecha, duración, modalidad y acceso, con un recordatorio 30 minutos antes. Los cambios y cancelaciones se actualizarán automáticamente después de sincronizar.</p>;
}
