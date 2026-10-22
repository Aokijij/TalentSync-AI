import { CalendarDays, Check, Columns3, ExternalLink, MapPin, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { JobInterestButtons } from "./JobInterests.jsx";
import { comparisonSalary, COMPARISON_LIMIT } from "../utils/jobComparison.js";
import { formatRelativeTime } from "../utils/dates.js";
import { externalPortal } from "../utils/externalPortal.js";
import "../styles/vacancy-card.css";

export function VacancyCard({ interests, comparison, job, match, confidence, applied, showMatch, returnTo }) {
  const selected = comparison?.ids.includes(job.id);
  const full = comparison && !selected && comparison.ids.length >= COMPARISON_LIMIT;
  const score = Math.max(0, Math.min(100, Number(match) || 0));
  const skills = [...new Set(job.skills || [])];
  return <article className={`vacancy-card${selected ? " is-compared" : ""}`}>
    <header><Link to={`/empresas/${job.company_id}`} className="vacancy-company">{job.company_name || "Empresa"}</Link>{comparison && <button type="button" className="vacancy-compare" aria-label={`${selected ? "Quitar de comparación" : "Comparar"}: ${job.title}`} aria-pressed={!!selected} title={full ? "Puedes comparar hasta 3 vacantes" : selected ? "Quitar de la comparación" : "Añadir a la comparación"} disabled={full} onClick={() => comparison.toggle(job.id)}>{selected ? <Check size={18} /> : <Columns3 size={18} />}</button>}</header>
    <h2><Link to={`/vacantes/${job.id}`} state={{ returnTo }}>{job.title}</Link></h2>
    <div className="vacancy-meta"><span className="vacancy-modality">{{ remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" }[job.modality] || "Modalidad por confirmar"}</span>{applied && <span className="vacancy-applied"><Check size={13} />Postulado</span>}<span><MapPin size={14} />{[job.location, job.department].filter(Boolean).join(", ") || "Ubicación flexible"}</span></div>
    <p className="vacancy-description">{job.description}</p>
    {!!skills.length && <ul className="vacancy-skills" aria-label="Habilidades solicitadas">{skills.slice(0, 3).map((skill) => <li key={skill}>{skill}</li>)}{skills.length > 3 && <li title={skills.slice(3).join(", ")}>+{skills.length - 3}</li>}</ul>}
    <div className="vacancy-salary"><strong>{comparisonSalary(job)}</strong></div>
    <div className="vacancy-bottom-meta"><span><CalendarDays size={13} />{formatRelativeTime(job.created_at)}</span>{showMatch && <span className="vacancy-score" title={job.source_kind === "external" ? `Estimación · confianza de datos ${Number(confidence ?? 0).toFixed(0)}%` : "Según tu perfil actual"}><Sparkles size={14} />{score.toFixed(0)}% {job.source_kind === "external" ? "estimado" : "compatible"}</span>}</div>
    {job.source_kind === "external" && <p className="vacancy-source"><ExternalLink size={12} />{externalPortal(job)}</p>}
    <footer>{interests?.enabled && <JobInterestButtons job={job} interests={interests} />}<Link to={`/vacantes/${job.id}`} state={{ returnTo }} className="button-primary button-sm">Ver oferta</Link></footer>
  </article>;
}
