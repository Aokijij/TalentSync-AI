import { ArrowRight, CalendarDays, Check, Columns3, ExternalLink, MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import { JobInterestButtons } from "./JobInterests.jsx";
import { ApplicationStatusNotice } from "./ApplicationStatusNotice.jsx";
import { CompatibilityBar } from "./CompatibilityBar.jsx";
import { comparisonSalary, COMPARISON_LIMIT } from "../utils/jobComparison.js";
import { formatRelativeTime } from "../utils/dates.js";
import { externalPortal } from "../utils/externalPortal.js";
import "../styles/vacancy-card.css";

export function VacancyCard({ interests, comparison, job, match, confidence, application, applied, showMatch, returnTo }) {
  const selected = comparison?.ids.includes(job.id);
  const full = comparison && !selected && comparison.ids.length >= COMPARISON_LIMIT;
  const hasMatch = match != null && match !== "" && Number.isFinite(Number(match));
  const score = hasMatch ? Math.max(0, Math.min(100, Number(match))) : null;
  const skills = [...new Set(job.skills || [])];
  const hasApplication = applied || Boolean(application);
  return <article className={`vacancy-card${selected ? " is-compared" : ""}${hasApplication ? " is-applied" : ""}`}>
    <header><Link to={`/empresas/${job.company_id}`} className="vacancy-company">{job.company_name || "Empresa"}</Link><span className="vacancy-modality">{{ remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" }[job.modality] || "Por confirmar"}</span></header>
    <h2><Link to={`/vacantes/${job.id}`} state={{ returnTo }}>{job.title}</Link></h2>
    <div className="vacancy-meta"><span><MapPin size={14} />{[job.location, job.department].filter(Boolean).join(", ") || "Ubicación por confirmar"}</span><span><CalendarDays size={14} />{formatRelativeTime(job.created_at)}</span></div>
    {showMatch && hasMatch && <div className="vacancy-match"><CompatibilityBar value={score} estimated={job.source_kind === "external"} confidence={confidence} compact /></div>}
    <p className="vacancy-description">{job.description}</p>
    {!!skills.length && <ul className="vacancy-skills" aria-label="Habilidades solicitadas">{skills.slice(0, 3).map((skill) => <li key={skill}>{skill}</li>)}{skills.length > 3 && <li title={skills.slice(3).join(", ")}>+{skills.length - 3}</li>}</ul>}
    <div className="vacancy-salary"><strong>{comparisonSalary(job)}</strong></div>
    {job.source_kind === "external" && <p className="vacancy-source"><ExternalLink size={12} />{externalPortal(job)}</p>}
    {hasApplication && <ApplicationStatusNotice application={application} compact />}
    {(interests?.enabled || comparison) && <div className={`vacancy-actions${interests?.enabled ? "" : " without-interests"}`}>
      {interests?.enabled && <JobInterestButtons job={job} interests={interests} />}
      {comparison && <button type="button" className="vacancy-compare" aria-label={`${selected ? "Quitar de comparación" : "Comparar"}: ${job.title}`} aria-pressed={!!selected} title={full ? "Puedes comparar hasta 3 vacantes" : selected ? "Quitar de la comparación" : "Añadir a la comparación"} disabled={full} onClick={() => comparison.toggle(job.id)}>{selected ? <Check size={15} /> : <Columns3 size={15} />}Comparar</button>}
    </div>}
    <footer><Link to={`/vacantes/${job.id}`} state={{ returnTo }} className={hasApplication ? "vacancy-detail-link" : "button-primary button-sm"}>Ver vacante{!hasApplication && <ArrowRight size={15} />}</Link>{hasApplication && <Link to={application?.id ? `/procesos/${application.id}` : "/postulaciones"} className="button-primary button-sm">{application?.id ? "Ver mi proceso" : "Mis postulaciones"}<ArrowRight size={15} /></Link>}</footer>
  </article>;
}
