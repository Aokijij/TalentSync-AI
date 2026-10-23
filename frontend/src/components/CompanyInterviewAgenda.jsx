import { useState } from "react";
import { CalendarClock, ChevronDown, Pencil } from "lucide-react";
import { activeInterview, interviewDateParts, processDate } from "../utils/interviewAgenda.js";
import { InterviewDetails } from "./InterviewDetails.jsx";
import "../styles/interview-agenda.css";

export function CompanyInterviewAgenda({ applications, loading, onManage }) {
  const [open, setOpen] = useState(false), [filter, setFilter] = useState("upcoming"), [query, setQuery] = useState("");
  const upcoming = applications.filter((row) => activeInterview(row));
  const rows = applications.filter((row) => row.interview_at && (filter === "all" || activeInterview(row)) && `${row.candidate_name || ""}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())).sort((a, b) => processDate(a.interview_at) - processDate(b.interview_at));
  return <section className="company-interview-agenda ui-panel">
    <button className="company-agenda-toggle" type="button" onClick={() => setOpen(!open)} aria-expanded={open}><CalendarClock size={22} /><span><strong>Gestionar entrevistas</strong><small>{loading ? "Cargando agenda…" : `${upcoming.length} próximas en esta vacante`}</small></span><ChevronDown size={18} /></button>
    {open && <div className="company-agenda-content"><div className="company-agenda-filters"><label>Buscar candidato<input className="field-control" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Nombre del candidato" /></label><label>Mostrar<select className="field-control" value={filter} onChange={(e) => setFilter(e.target.value)}><option value="upcoming">Próximas entrevistas</option><option value="all">Todas las programadas</option></select></label></div>
      <p className="schedule-save-note">Hora de Colombia. Puedes cambiar fecha, modalidad y acceso desde cada entrevista. Para programar una nueva, abre «Gestionar proceso» en un candidato del tablero.</p>
      {rows.map((row) => <article key={row.id}><div><h3>{row.candidate_name}</h3><p>{interviewDateParts(row.interview_at)?.full} · <strong>{interviewDateParts(row.interview_at)?.time}</strong></p><InterviewDetails details={row.interview_details} />{!activeInterview(row) && <small>Fecha pasada o proceso finalizado</small>}</div><button type="button" className="button-secondary button-sm" onClick={() => onManage(row)}><Pencil size={15} />Gestionar entrevista</button></article>)}
      {!rows.length && <p className="learning-empty">No hay entrevistas con estos filtros.</p>}
    </div>}
  </section>;
}
