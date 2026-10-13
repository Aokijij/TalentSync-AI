import { formatLearningHours } from "../utils/learningPresentation.js";
import { useEffect, useState } from "react";
import { Download, ExternalLink, Library } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

export function LearnCatalogImport({ onImported }) {
  const [configured, setConfigured] = useState(null);
  const [kind, setKind] = useState("modules"), [products, setProducts] = useState("");
  const [preview, setPreview] = useState(null), [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  useEffect(() => {
    api.get("/admin/learning/sources").then(({ data }) => setConfigured(data.microsoft_learn.configured))
      .catch((failure) => setError(getApiErrorMessage(failure)));
  }, []);
  async function consult(cursor = "") {
    setBusy(true); setError(""); setNotice("");
    try {
      const { data } = await api.post("/admin/learning/sources/microsoft-learn/preview", { kind, products, cursor }, { __quiet: true });
      setPreview(data); setSelected([]);
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function importDrafts() {
    setBusy(true); setError(""); setNotice("");
    try {
      const { data } = await api.post("/admin/learning/sources/microsoft-learn/import", { preview_id: preview.preview_id, ids: selected });
      onImported(data.resources); setSelected([]);
      setNotice(`${data.created} borradores importados · ${data.existing} ya estaban en el catálogo. Revisa sus habilidades y activa cada recurso desde Editar.`);
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  function resetFilters() { setPreview(null); setSelected([]); setNotice(""); }
  return <section className="surface-card p-5 sm:p-6" aria-labelledby="learn-import-title">
    <div className="flex flex-wrap items-start justify-between gap-4"><div className="flex gap-3"><span className="learning-area-icon shrink-0"><Library size={22} /></span><div>
      <p className="section-kicker">Catálogo conectado</p><h2 id="learn-import-title" className="mt-1 text-lg font-bold">Microsoft Learn</h2>
      <p className="mt-1 max-w-2xl text-sm leading-6 text-[var(--muted)]">Consulta módulos y rutas. Selecciona la formación útil e impórtala como borrador para revisar su relación con las habilidades.</p>
    </div></div><span className="status-chip">{configured === null ? "Comprobando configuración" : configured ? "Configurado · pendiente de consultar" : "Pendiente de credenciales"}</span></div>
    {error && <p role="alert" className="mt-4 text-sm text-[var(--error)]">{error}</p>}
    {notice && <p role="status" className="mt-4 rounded-xl bg-[var(--panel)] p-4 text-sm">{notice}</p>}
    {configured ? <>
      <form className="mt-5 flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); consult(); }}>
        <label className="min-w-48 flex-1 text-sm">Formación<select className="field-control mt-1" value={kind} disabled={busy} onChange={(event) => { setKind(event.target.value); resetFilters(); }}><option value="modules">Módulos</option><option value="learning-paths">Rutas de aprendizaje</option></select></label>
        <label className="min-w-48 flex-1 text-sm">Producto (opcional)<input className="field-control mt-1" placeholder="Ej. power-bi, azure" maxLength={120} pattern="[a-z0-9,-]*" value={products} disabled={busy} onChange={(event) => { setProducts(event.target.value); resetFilters(); }} /></label>
        <button className="button-secondary" disabled={busy}>{busy ? "Consultando…" : "Consultar catálogo"}</button>
      </form>
      {preview && <div className="mt-5 border-t border-[var(--line)] pt-4"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-bold">{preview.resources.length} recursos para revisar</h3><span className="text-xs text-[var(--muted)]">Vista previa válida durante 10 minutos</span></div>
        {preview.skipped > 0 && <p className="mt-2 text-xs text-[var(--muted)]">Se omitieron {preview.skipped} registros incompletos o incompatibles.</p>}
        {!preview.resources.length && <p className="my-4 text-sm text-[var(--muted)]">No hay recursos importables en esta página. Prueba otro producto o consulta la siguiente página.</p>}
        <div className="mt-3 max-h-96 divide-y divide-[var(--line)] overflow-y-auto">{preview.resources.map((row) => <div className="flex items-start gap-3 py-4" key={row.source_id}>
          <input className="mt-1" type="checkbox" aria-label={`Seleccionar ${row.content.title}`} disabled={busy} checked={selected.includes(row.source_id)} onChange={(event) => setSelected(event.target.checked ? [...selected, row.source_id] : selected.filter((id) => id !== row.source_id))} />
          <div className="min-w-0"><a className="inline-flex items-center gap-2 font-bold text-[var(--accent)]" href={row.content.url} target="_blank" rel="noreferrer">{row.content.title}<ExternalLink size={14} className="shrink-0" /></a>
          <p className="mt-1 text-xs text-[var(--muted)]">{formatLearningHours(row.content.hours)} h · Gratuito · {row.source.locale}</p><p className="mt-2 text-sm leading-6 text-[var(--muted)]">{row.content.instructions}</p>
          <p className="mt-2 text-xs">Etiquetas a revisar: {row.content.skills.join(", ")}</p></div>
        </div>)}</div>
        <div className="mt-4 flex flex-wrap items-center gap-3"><button className="button-primary" disabled={busy || !selected.length} onClick={importDrafts}><Download size={16} />Importar {selected.length || "selección"} como borrador</button>{preview.next_cursor && <button className="button-secondary" disabled={busy} onClick={() => consult(preview.next_cursor)}>Siguiente página</button>}</div>
      </div>}
    </> : configured === false && <div className="mt-5 rounded-xl border border-[var(--line)] p-4 text-sm leading-6"><strong>El conector está preparado.</strong><p className="mt-1 text-[var(--muted)]">Para activarlo, configura en el servidor el tenant, el identificador y el secreto de una aplicación de Microsoft Entra con acceso a Learn. Las credenciales se guardan fuera del navegador.</p></div>}
    <p className="mt-4 text-xs leading-5 text-[var(--muted)]">Se consulta al pulsar el botón. Importar formación no acredita haberla completado ni verifica certificados. El candidato estudia en Microsoft Learn y aporta el comprobante del emisor cuando corresponda.</p>
  </section>;
}
