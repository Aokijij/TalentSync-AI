import "../styles/learning-discovery.css";
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
  if (compact) return <><article className="learning-resource-compact learning-course-card">
    <header><span className="learning-area-icon"><AreaIcon area={resource.category} /></span><div><p className="course-card-provider">{resource.provider || (resource.url ? "Formación externa" : "TalentSync")}</p><h4><button className="resource-title-button" onClick={() => setDetails(true)}>{resource.title}</button></h4></div></header>
    <div className="course-card-body"><div className="course-card-meta"><span><Clock3 size={13} />{formatLearningHours(resource.hours)} h</span><span className={`course-card-cost${resource.cost === "free" ? " is-free" : ""}`}>{resource.cost === "paid" ? "De pago" : resource.cost === "free" ? "Gratuito" : "Coste por confirmar"}</span><span>{resource.url ? "Curso externo" : "Práctica en TalentSync"}</span></div>
    <div className="course-target-skills"><strong>Refuerza</strong><div>{(resource.targeted_skills || resource.skills || []).map((skill) => <span key={skill}>{skill}</span>)}</div></div></div>
    <footer><button type="button" className="button-secondary button-sm" onClick={() => setDetails(true)}>Ver contenido<ArrowRight size={14} /></button>{onPlan && (inPlan ? <Link className="button-secondary button-sm" to="/aprendizaje#mi-plan"><Check size={14} />En mi plan</Link> : <button type="button" className="button-primary button-sm" disabled={busy || resource.active === false} onClick={() => onPlan(resource.id)}>Añadir a mi plan<ArrowRight size={14} /></button>)}</footer>
  </article>{dialog}</>;
  return <><article className="learning-resource">
    <div className="flex items-center justify-between gap-3"><span className="learning-area-icon"><AreaIcon area={resource.category} /></span><span className="learning-tag">{resource.url ? "Formación externa" : "Práctica guiada"}</span></div>
    <h3 className="text-lg font-bold"><button className="resource-title-button text-left" onClick={() => setDetails(true)}>{resource.title}</button></h3>
    <p className="text-sm text-[var(--muted)]">{resource.url ? resource.instructions : resource.journey?.activities ? `Laboratorio inicial: ${resource.journey.lab_title}. Ordena, calcula y relaciona conceptos con correcciones.` : resource.journey?.outcome || resource.instructions}</p>
    <div className="flex flex-wrap gap-2 text-xs">{(resource.targeted_skills || resource.skills).map((skill) => <span className="learning-skill" key={skill}>{skill}</span>)}</div>
    <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--muted)]"><span className="inline-flex items-center gap-1"><Clock3 size={14} />{formatLearningHours(resource.hours)} h estimadas</span><span>{resource.cost === "paid" ? "De pago" : resource.cost === "unknown" ? "Coste por confirmar" : "Gratuito"}</span><span>{resource.provider}</span></div>
    {resource.details && <div className="space-y-2 rounded-xl border border-[var(--border)] p-3 text-xs text-[var(--muted)]"><p>{learningLevels[resource.details.level]} · {learningLanguages(resource.details.languages) || "Consultar idiomas"}</p><p className="font-semibold text-[var(--accent)]">{certificateCosts[resource.details.certificate_cost]}</p><p>{resource.details.access_notes}</p></div>}
    {resource.relevance?.reasons?.length > 0 && <div className="learning-relevance"><strong>{resource.relevance.kind === "complementary" ? "Para explorar" : "Por qué aparece para ti"}</strong>{resource.relevance.reasons.slice(0, 2).map((reason) => <p key={reason}>{reason}</p>)}</div>}
    <CourseEnrollment resource={resource} compact />
    {(resource.sponsored || resource.affiliate) && <p className="text-xs"><strong>{resource.sponsored ? "Patrocinado" : "Enlace afiliado"}:</strong> {resource.disclosure}</p>}
    {resource.projected_match !== undefined && <div className="learning-projection"><strong>Escenario al acreditar: {resource.projected_match.toFixed(1)}%</strong><span>{resource.estimated_gain.toFixed(1)} puntos de cambio · {resource.other_jobs_impacted} otras vacantes con requisitos relacionados</span><small>{resource.notice}</small></div>}
    <div className="mt-auto flex flex-wrap gap-3 pt-2"><button className="button-secondary" onClick={() => setDetails(true)}>Ver detalle</button>{resource.url && <a className="button-outline" href={resource.url} target="_blank" rel={resource.sponsored || resource.affiliate ? "noopener noreferrer sponsored" : "noopener noreferrer"}>Ver curso<ExternalLink size={15} /></a>}{onPlan && (inPlan ? <Link className="button-secondary" to="/aprendizaje#mi-plan"><Check size={16} />En mi plan</Link> : <button disabled={busy || resource.active === false} className="button-primary" onClick={() => onPlan(resource.id)}>Añadir a mi plan<ArrowRight size={16} /></button>)}</div>
  </article>{dialog}</>;
}
