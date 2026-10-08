import { useState } from "react";
import { Link } from "react-router-dom";
import { pageItems, totalPages } from "../utils/pagination.js";
import { searchJob } from "../utils/jobDiscovery.js";

export function JobInterestButtons({ job, interests }) {
  if (!interests.enabled) return null;
  const state = interests.byId.get(job.id);
  return <div className="mt-3 flex flex-wrap gap-3 text-sm">
    <button disabled={interests.busy} aria-pressed={state === true} className="text-[var(--accent)]" onClick={() => state === true ? interests.remove(job.id) : interests.save(job.id, true)}>{state === true ? "✓ Guardada · quitar" : "Guardar vacante"}</button>
    <button disabled={interests.busy} className="text-[var(--muted)]" onClick={() => state === false ? interests.remove(job.id) : interests.save(job.id, false)}>{state === false ? "Restaurar vacante" : "No me interesa"}</button>
  </div>;
}

export function InterestsSettings({ interests, jobs, embedded = false }) {
  const [query, setQuery] = useState(""), [page, setPage] = useState(1);
  const hidden = jobs.filter((job) => interests.byId.get(job.id) === false && searchJob(job, query));
  const pages = totalPages(hidden, 5);
  const Container = embedded ? "div" : "details";
  return <Container className="surface-card p-4" id="mis-intereses">{!embedded && <summary className="cursor-pointer font-semibold">Personalizar y recuperar vacantes ocultas</summary>}<div className="mt-3 space-y-3">
    <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={interests.enabled} disabled={interests.busy || !interests.privacy} onChange={(event) => interests.consent(event.target.checked)} />Usar mis decisiones de guardar u ocultar para personalizar recomendaciones.</label><p className="text-xs text-[var(--muted)]">Solo se usan decisiones explícitas; no tu navegación. Desactivar elimina estas decisiones y los modelos experimentales que las incluyan. La compatibilidad conserva su cálculo independiente.</p>
    {interests.error && <p role="alert" className="text-sm text-[var(--error)]">{interests.error}</p>}{interests.notice && <p role="status" className="text-sm">{interests.notice}</p>}
    {interests.enabled && <><label className="block text-sm">Buscar entre ocultas<input className="field-control mt-1" value={query} placeholder="Cargo, empresa, ubicación o habilidad" onChange={(event) => { setQuery(event.target.value); setPage(1); }} /></label><p className="text-sm">{hidden.length} vacantes ocultas</p>{pageItems(hidden, Math.min(page, pages), 5).map((job) => <article className="border-t border-[var(--line)] pt-3" key={job.id}><Link className="font-semibold" to={`/vacantes/${job.id}`}>{job.title}</Link><p className="text-xs text-[var(--muted)]">{job.company_name} · {job.location}</p><button disabled={interests.busy} className="text-sm text-[var(--accent)]" onClick={() => interests.remove(job.id)}>Restaurar en recomendaciones</button></article>)}{pages > 1 && <div className="flex items-center gap-3"><button className="button-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button><span>{Math.min(page, pages)} / {pages}</span><button className="button-secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>Siguiente</button></div>}</>}
  </div></Container>;
}
