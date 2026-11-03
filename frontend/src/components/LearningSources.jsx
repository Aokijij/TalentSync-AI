import { useState } from "react";
import { Link } from "react-router-dom";
import { Info, ChevronDown, ArrowUpRight, MapPin } from "lucide-react";

const dateLabel = (value) => new Date(value.length === 10 ? `${value}T12:00:00` : value).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });
export function LearningSources({ radar }) {
  const [more, setMore] = useState(false);
  return <details className="learning-sources"><summary><span className="learning-source-icon"><Info size={20} /></span><span><strong>¿De dónde salen estas sugerencias?</strong><small>Consulta las ofertas y fuentes que usamos</small></span><ChevronDown size={18} /></summary><div className="learning-sources-body">
    <div className="learning-source-stats"><div><small>Ofertas analizadas</small><strong>{radar.sample}</strong></div><div><small>Periodo observado</small><strong>Últimos 90 días</strong><span>Desde el {dateLabel(radar.since)}</span></div><div><small>Última consulta</small><strong>{dateLabel(radar.as_of)}</strong></div></div>
    <p>{radar.note}</p>{radar.small_sample && <p className="learning-sample-note">La muestra es pequeña: mostramos el número de ofertas, sin porcentajes.</p>}
    <div className="learning-source-tags">{Object.entries(radar.sources).map(([name, count]) => <span key={name}>{name === "local-quality-demo" ? "Demostración local" : name}<b>{count}</b></span>)}</div>
    {!!radar.jobs.length && <><h4>Explora algunas ofertas de la muestra</h4><div className="learning-source-jobs">{radar.jobs.slice(0, more ? radar.jobs.length : 4).map((job) => <Link key={job.id} to={`/vacantes/${job.id}`}><span><strong>{job.title}</strong><small><MapPin size={12} />{job.location || "Ubicación por consultar"}</small></span><ArrowUpRight size={16} /></Link>)}</div>{radar.jobs.length > 4 && <button type="button" className="learning-source-more" aria-expanded={more} onClick={() => setMore((value) => !value)}>{more ? "Ver menos ofertas" : `Ver las ${radar.jobs.length} ofertas de ejemplo`}<ChevronDown size={15} /></button>}</>}
  </div></details>;
}
