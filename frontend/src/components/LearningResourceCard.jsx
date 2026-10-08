export function LearningResourceCard({ resource, busy, onPlan }) {
  return <article className="space-y-3 rounded-lg border border-[var(--line)] p-4">
    <h3 className="font-bold">{resource.title}</h3>
    <p className="text-xs text-[var(--muted)]">{resource.provider} · {resource.hours} h estimadas · {{ free: "Gratuito", paid: "De pago", unknown: "Coste por confirmar" }[resource.cost] || "Proyecto local"}{resource.active === false && " · Archivado"}</p>
    {(resource.sponsored || resource.affiliate) && <p className="rounded bg-[var(--surface-subtle)] p-2 text-sm"><strong>{resource.sponsored ? "Patrocinado" : "Enlace afiliado"}{resource.sponsored && resource.affiliate ? " · Enlace afiliado" : ""}:</strong> {resource.disclosure}</p>}
    <p className="text-sm">{resource.instructions}</p>
    <p className="text-sm">Habilidades: {(resource.targeted_skills || resource.skills).join(", ")}</p>
    {resource.projected_match !== undefined && <><p className="font-semibold">Escenario al acreditar: {resource.projected_match.toFixed(1)}% (+{resource.estimated_gain.toFixed(1)} puntos)</p><p className="text-xs text-[var(--muted)]">{resource.notice} Puede mejorar el índice en {resource.other_jobs_impacted} vacantes examinadas.</p></>}
    {resource.assessment_ids?.length > 0 && <p className="text-xs text-[var(--muted)]">Hay una microprueba de fundamentos para: {resource.assessment_ids.join(", ")}. Puedes iniciarla en esta página; terminar un curso no la aprueba automáticamente.</p>}
    <div className="flex flex-wrap gap-3">{resource.url && <a className="button-outline inline-flex" href={resource.url} target="_blank" rel="noopener noreferrer sponsored">Ver recurso externo</a>}{onPlan && <button disabled={busy || resource.active === false} className="button-secondary" onClick={() => onPlan(resource.id)}>Añadir a mi plan</button>}</div>
  </article>;
}
