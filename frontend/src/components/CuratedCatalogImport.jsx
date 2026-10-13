import { formatLearningHours } from "../utils/learningPresentation.js";
import { useState } from "react";
import { BookOpen, ExternalLink, LibraryBig } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { LearningFilters } from "./LearningFilters.jsx";
import { Pagination } from "./Pagination.jsx";
import { filterResources } from "../utils/learningFilters.js";
import { certificateCosts } from "../utils/learningPresentation.js";

export function CuratedCatalogImport({ onImported }) {
  const [catalog, setCatalog] = useState(null), [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({}), [page, setPage] = useState(1);
  const [selected, setSelected] = useState([]), [publish, setPublish] = useState(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  async function explore() {
    setOpen(!open); if (catalog || open) return;
    setBusy(true); setError("");
    try { setCatalog((await api.get("/admin/learning/sources/curated")).data); }
    catch (failure) { setError(getApiErrorMessage(failure)); setOpen(false); }
    finally { setBusy(false); }
  }
  const resources = (catalog?.resources || []).map((row) => ({ ...row.content, id: row.source_id }));
  const filtered = filterResources(resources, filters), pages = Math.max(1, Math.ceil(filtered.length / 8));
  const safePage = Math.min(page, pages), visible = filtered.slice((safePage - 1) * 8, safePage * 8);
  function toggle(id) { setSelected((prior) => prior.includes(id) ? prior.filter((key) => key !== id) : [...prior, id]); }
  async function importCourses() {
    setBusy(true); setError(""); setMessage("");
    try {
      const { data } = await api.post("/admin/learning/sources/curated/import", { revision: catalog.revision, ids: selected, publish });
      onImported(data.resources); setSelected([]);
      setMessage(`${data.created} recursos añadidos ${publish ? "y publicados" : "como borradores"} · ${data.existing} ya existían y conservaron sus cambios.`);
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="surface-card space-y-4 p-5">
    <div className="flex flex-wrap items-center justify-between gap-4"><div className="flex items-start gap-3"><span className="learning-area-icon"><LibraryBig size={23} /></span><div><p className="section-kicker">Fuentes educativas</p><h2 className="mt-1 text-xl font-bold">Una biblioteca para distintas profesiones</h2><p className="mt-2 text-sm text-[var(--muted)]">SENA, HP LIFE, Microsoft, Google y más. Cursos gratuitos y de pago con condiciones de certificación.</p></div></div><button className="button-secondary" aria-expanded={open} disabled={busy} onClick={explore}>{open ? "Cerrar fuentes" : "Explorar fuentes"}</button></div>
    <p className="text-xs text-[var(--muted)]">Selección editorial con enlaces oficiales. No se sincroniza automáticamente ni importa compras, alumnos o certificados.</p>
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}{message && <p role="status" className="learning-published">{message}</p>}
    {open && catalog && <><div className="flex flex-wrap gap-2">{catalog.providers.map((provider) => <span key={provider.id} className="learning-skill">{provider.name} · {provider.count}</span>)}</div><p className="text-xs text-[var(--muted)]">{resources.length} recursos · {resources.filter((row) => row.cost === "free").length} gratuitos · revisión: {catalog.reviewed_at}</p>
      <LearningFilters value={filters} resources={resources} onChange={(next) => { setFilters(next); setPage(1); }} />
      <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-bold">{filtered.length} recursos encontrados</h3><div className="flex flex-wrap gap-2"><button disabled={busy || !visible.length} className="button-secondary button-sm" onClick={() => setSelected([...new Set([...selected, ...visible.map((row) => row.id)])])}>Seleccionar página</button><button disabled={busy || !selected.length} className="button-secondary button-sm" onClick={() => setSelected([])}>Limpiar selección ({selected.length})</button></div></div>
      <div className="grid gap-3 lg:grid-cols-2">{visible.map((row) => <article key={row.id} className="rounded-2xl border border-[var(--border)] p-4"><label className="flex items-start gap-3"><input type="checkbox" className="mt-1" disabled={busy} checked={selected.includes(row.id)} onChange={() => toggle(row.id)} /><span className="min-w-0"><strong className="block">{row.title}</strong><span className="mt-1 block text-xs text-[var(--muted)]">{row.provider} · {formatLearningHours(row.hours)} h estimadas · {row.cost === "free" ? "Acceso gratuito" : "De pago"}</span></span></label><p className="mt-3 text-sm text-[var(--muted)]">{row.instructions}</p><p className="mt-2 text-xs font-semibold text-[var(--accent)]">{certificateCosts[row.details.certificate_cost]}</p><a className="mt-3 inline-flex items-center gap-2 text-xs text-[var(--accent)]" href={row.url} target="_blank" rel="noopener noreferrer">Revisar fuente oficial<ExternalLink size={13} /></a></article>)}</div>
      {filtered.length === 0 && <p role="status" className="learning-empty">No hay cursos con esos filtros.</p>}
      <Pagination page={safePage} pages={pages} total={filtered.length} pageSize={8} onChange={setPage} label="Páginas de fuentes educativas" />
      <div className="space-y-3 border-t border-[var(--border)] pt-4"><label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={publish} disabled={busy} onChange={(event) => setPublish(event.target.checked)} />Publicar los nuevos recursos seleccionados para los candidatos</label><p className="text-xs text-[var(--muted)]">Al desmarcar, se importan como borradores. Los recursos ya importados conservan su estado y sus ediciones.</p><button className="button-primary" disabled={busy || !selected.length} onClick={importCourses}><BookOpen size={16} />{busy ? "Importando…" : `Importar ${selected.length} ${publish ? "y publicar" : "como borradores"}`}</button></div>
    </>}
  </section>;
}
