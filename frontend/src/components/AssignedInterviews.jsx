import { useState } from "react";
import { CalendarClock, ArrowUpRight, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { Pagination } from "./Pagination.jsx";
export function AssignedInterviews({ assignments }) {
  const [query, setQuery] = useState(""), [jobFilter, setJobFilter] = useState("all"), [stage, setStage] = useState("all"), [page, setPage] = useState(1);
  const rows = assignments.flatMap((job) => job.applications.map((row) => ({ ...row, job })));
  const stages = [...new Set(rows.map((row) => row.stage_title))];
  const filtered = rows.filter((row) => (jobFilter === "all" || String(row.job.job_id) === jobFilter) && (stage === "all" || row.stage_title === stage) && `${row.job.title} ${row.candidate_alias}`.toLocaleLowerCase("es").includes(query.toLocaleLowerCase("es")));
  const pages = Math.max(1, Math.ceil(filtered.length / 8)), safePage = Math.min(page, pages);
  return <section className="space-y-4"><header className="section-heading"><div><h2 className="text-xl font-bold">Tus procesos asignados</h2><p className="mt-1 text-sm text-[var(--muted)]">{assignments.length} vacantes · {rows.length} personas. Abre un proceso para preparar la entrevista y evaluar.</p></div></header>
    <div className="compact-filterbar"><label>Buscar<span className="search-control"><Search size={16} /><input placeholder="Vacante o candidato" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} /></span></label><label>Vacante<select className="field-control" value={jobFilter} onChange={(event) => { setJobFilter(event.target.value); setPage(1); }}><option value="all">Todas las asignadas</option>{assignments.map((job) => <option key={job.job_id} value={job.job_id}>{job.title}</option>)}</select></label><label>Etapa<select className="field-control" value={stage} onChange={(event) => { setStage(event.target.value); setPage(1); }}><option value="all">Todas las etapas</option>{stages.map((title) => <option key={title}>{title}</option>)}</select></label></div>
    <div className="surface-card assigned-list">{filtered.slice((safePage - 1) * 8, safePage * 8).map((row) => <article className="assigned-row" key={row.id}><div className="min-w-0"><p className="text-xs text-[var(--muted)]">{row.job.title}</p><h3 className="mt-1 font-bold">{row.candidate_alias}</h3></div><span className="status-chip">{row.stage_title}</span><p className="inline-flex items-center gap-2 text-xs text-[var(--muted)]"><CalendarClock size={15} />{row.interview_at ? new Date(row.interview_at.endsWith("Z") ? row.interview_at : `${row.interview_at}Z`).toLocaleString("es-CO") : "Sin entrevista programada"}</p><Link className="button-secondary button-sm" to={`/procesos/${row.id}`}>Abrir proceso<ArrowUpRight size={14} /></Link></article>)}{!filtered.length && <p className="learning-empty">No hay procesos con estos filtros. El propietario puede asignarte vacantes desde Equipo.</p>}</div>
    <Pagination page={safePage} pages={pages} total={filtered.length} pageSize={8} onChange={setPage} label="Páginas de procesos asignados" />
  </section>;
}
