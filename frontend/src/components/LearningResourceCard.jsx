import { formatLearningHours } from "../utils/learningPresentation.js";
import { useCallback, useState } from "react";
import { ResourceDetailsDialog } from "./ResourceDetailsDialog.jsx";
import { ArrowRight, Check, Clock3, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { AreaIcon } from "./LearningVisuals.jsx";
import { certificateCosts, learningLanguages, learningLevels } from "../utils/learningPresentation.js";
import { CourseEnrollment } from "./CourseEnrollment.jsx";

export function LearningResourceCard({ resource, busy, onPlan, inPlan = false, compact = false }) {
  const [details, setDetails] = useState(false);
  const closeDetails = useCallback(() => setDetails(false), []);
  const dialog = details && <ResourceDetailsDialog resource={resource} onClose={closeDetails} onPlan={onPlan} inPlan={inPlan} busy={busy} />;
  if (compact) return <><article className="learning-resource-compact"><span className="learning-area-icon"><AreaIcon area={resource.category} /></span><div className="min-w-0 flex-1"><button className="resource-title-button text-left text-sm font-bold" onClick={() => setDetails(true)}>{resource.title}</button><p className="mt-1 text-xs text-[var(--muted)]">{formatLearningHours(resource.hours)} h · {resource.cost === "paid" ? "De pago" : resource.cost === "free" ? "Gratuito" : "Coste por confirmar"} · {resource.url ? "Externo" : "TalentSync"}</p><button className="mt-2 text-xs font-semibold text-[var(--accent)]" onClick={() => setDetails(true)}>Contenido y aporte a mi perfil →</button></div>{onPlan && (inPlan ? <Link className="button-secondary button-sm" to="/aprendizaje#mi-plan"><Check size={14} />En mi plan</Link> : <button className="button-primary button-sm" disabled={busy || resource.active === false} onClick={() => onPlan(resource.id)}>Añadir<ArrowRight size={14} /></button>)}</article>{dialog}</>;
  return <><article className="learning-resource">
    <div className="flex items-center justify-between gap-3"><span className="learning-area-icon"><AreaIcon area={resource.category} /></span><span className="learning-tag">{resource.url ? "Formación externa" : "Práctica guiada"}</span></div>
    <h3 className="text-lg font-bold"><button className="resource-title-button text-left" onClick={() => setDetails(true)}>{resource.title}</button></h3>
    <p className="text-sm text-[var(--muted)]">{resource.url ? resource.instructions : resource.journey?.activities ? `Laboratorio inicial: ${resource.journey.lab_title}. Ordena, calcula y relaciona conceptos con correcciones.` : resource.journey?.outcome || resource.instructions}</p>
    <div className="flex flex-wrap gap-2 text-xs">{(resource.targeted_skills || resource.skills).map((skill) => <span className="learning-skill" key={skill}>{skill}</span>)}</div>
    <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]"><span className="inline-flex items-center gap-1"><Clock3 size={14} />{formatLearningHours(resource.hours)} h estimadas</span><span>{resource.cost === "paid" ? "De pago" : resource.cost === "unknown" ? "Coste por confirmar" : "Gratuito"}</span><span>{resource.provider}</span></div>
    {resource.details && <div className="space-y-2 rounded-xl border border-[var(--border)] p-3 text-xs text-[var(--muted)]"><p>{learningLevels[resource.details.level]} · {learningLanguages(resource.details.languages) || "Consultar idiomas"}</p><p className="font-semibold text-[var(--accent)]">{certificateCosts[resource.details.certificate_cost]}</p><p>{resource.details.access_notes}</p></div>}
    <CourseEnrollment resource={resource} compact />
    {(resource.sponsored || resource.affiliate) && <p className="text-xs"><strong>{resource.sponsored ? "Patrocinado" : "Enlace afiliado"}:</strong> {resource.disclosure}</p>}
    {resource.projected_match !== undefined && <div className="learning-projection"><strong>Escenario al acreditar: {resource.projected_match.toFixed(1)}%</strong><span>{resource.estimated_gain.toFixed(1)} puntos de cambio · {resource.other_jobs_impacted} otras vacantes con requisitos relacionados</span><small>{resource.notice}</small></div>}
    <div className="mt-auto flex flex-wrap gap-3 pt-2"><button className="button-secondary" onClick={() => setDetails(true)}>Ver detalle</button>{resource.url && <a className="button-outline" href={resource.url} target="_blank" rel={resource.sponsored || resource.affiliate ? "noopener noreferrer sponsored" : "noopener noreferrer"}>Ver curso<ExternalLink size={15} /></a>}{onPlan && (inPlan ? <Link className="button-secondary" to="/aprendizaje#mi-plan"><Check size={16} />En mi plan</Link> : <button disabled={busy || resource.active === false} className="button-primary" onClick={() => onPlan(resource.id)}>Añadir a mi plan<ArrowRight size={16} /></button>)}</div>
  </article>{dialog}</>;
}
