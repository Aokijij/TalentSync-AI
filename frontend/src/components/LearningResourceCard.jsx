import { ArrowRight, Check, Clock3, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { AreaIcon } from "./LearningVisuals.jsx";

export function LearningResourceCard({ resource, busy, onPlan, inPlan = false }) {
  return <article className="learning-resource">
    <div className="flex items-center justify-between gap-3"><span className="learning-area-icon"><AreaIcon area={resource.category} /></span><span className="learning-tag">{resource.url ? "Formación externa" : "Práctica guiada"}</span></div>
    <h3 className="text-lg font-bold">{resource.title}</h3>
    <p className="text-sm text-[var(--muted)]">{resource.journey?.activities ? `Laboratorio inicial: ${resource.journey.lab_title}. Ordena, calcula y relaciona conceptos con correcciones.` : resource.journey?.outcome || resource.instructions}</p>
    <div className="flex flex-wrap gap-2 text-xs">{(resource.targeted_skills || resource.skills).map((skill) => <span className="learning-skill" key={skill}>{skill}</span>)}</div>
    <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]"><span className="inline-flex items-center gap-1"><Clock3 size={14} />{resource.hours} h estimadas</span><span>{resource.cost === "paid" ? "De pago" : resource.cost === "unknown" ? "Coste por confirmar" : "Gratuito"}</span><span>{resource.provider}</span></div>
    {resource.url && <details className="text-xs text-[var(--muted)]"><summary className="cursor-pointer">Temario y condiciones del recurso</summary><p className="mt-2">{resource.instructions}</p></details>}
    {(resource.sponsored || resource.affiliate) && <p className="text-xs"><strong>{resource.sponsored ? "Patrocinado" : "Enlace afiliado"}:</strong> {resource.disclosure}</p>}
    {resource.projected_match !== undefined && <div className="learning-projection"><strong>Escenario al acreditar: {resource.projected_match.toFixed(1)}%</strong><span>+{resource.estimated_gain.toFixed(1)} puntos · {resource.other_jobs_impacted} otras vacantes examinadas</span><small>{resource.notice}</small></div>}
    <div className="mt-auto flex flex-wrap gap-3 pt-2">{resource.url && <a className="button-outline" href={resource.url} target="_blank" rel={resource.sponsored || resource.affiliate ? "noopener noreferrer sponsored" : "noopener noreferrer"}>Ver curso<ExternalLink size={15} /></a>}{onPlan && (inPlan ? <Link className="button-secondary" to="/aprendizaje#mi-plan"><Check size={16} />En mi plan</Link> : <button disabled={busy || resource.active === false} className="button-primary" onClick={() => onPlan(resource.id)}>Añadir a mi plan<ArrowRight size={16} /></button>)}</div>
  </article>;
}
