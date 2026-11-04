import { useEffect, useState } from "react";
import { RefreshCw, Trash2 } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { Pagination } from "./Pagination.jsx";
const reasons = { closed_at_source: "Cerrada en la fuente", expired: "Plazo vencido", old_publication: "Publicación fuera del periodo admitido", missing_original_url: "Sin enlace original", empty_content: "Sin contenido aprovechable" };

export function CatalogCleanupPanel({ onChanged }) {
  const { confirm } = useFeedback();
  const [data, setData] = useState(null), [selected, setSelected] = useState(new Set()), [page, setPage] = useState(1), [busy, setBusy] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  async function load() { try { setError(""); setData((await api.get("/admin/jobs/cleanup")).data); setSelected(new Set()); } catch (failure) { setError(getApiErrorMessage(failure)); } }
  useEffect(() => { load(); }, []);
  const rows = data?.items || [], pages = Math.max(1, Math.ceil(rows.length / 10)), safePage = Math.min(page, pages);
  async function remove() {
    if (!await confirm({ title: "Eliminar ofertas sin utilidad", description: `Se eliminarán hasta ${selected.size} ofertas seleccionadas. Se comprueba de nuevo su estado y se conservan las ofertas útiles o con postulaciones. Las descartadas no se vuelven a importar automáticamente.`, confirmLabel: "Eliminar seleccionadas", destructive: true })) return;
    setBusy(true); setError("");
    try { const { data: result } = await api.post("/admin/jobs/cleanup", { ids: [...selected] }, { __skipRetry: true }); setNotice(`${result.deleted} ofertas eliminadas. ${result.skipped.length} se conservaron al volver a comprobarlas.`); await load(); await onChanged(); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <section className="admin-cleanup-panel"><header><div><h3>Limpieza del catálogo</h3><p>La revisión identifica ofertas cerradas, vencidas, demasiado antiguas o sin contenido aprovechable. Un fallo temporal de conexión no se considera motivo de eliminación.</p></div><button type="button" className="button-secondary button-sm" disabled={busy} onClick={load}><RefreshCw size={15} />Actualizar revisión</button></header>{error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}{!data && !error && <p role="status">Revisando los registros…</p>}{data && <><div className="admin-cleanup-actions"><label><input type="checkbox" disabled={busy || !rows.length} checked={!!rows.length && selected.size === rows.length} onChange={e => setSelected(e.target.checked ? new Set(rows.map(r => r.id)) : new Set())} />Seleccionar elegibles ({data.total})</label><button type="button" className="button-secondary" disabled={busy || !selected.size} onClick={remove}><Trash2 size={15} />Eliminar seleccionadas ({selected.size})</button></div>{rows.slice((safePage - 1) * 10, safePage * 10).map(row => <label className="admin-cleanup-row" key={row.id}><input type="checkbox" checked={selected.has(row.id)} disabled={busy} onChange={e => setSelected(current => { const next = new Set(current); if (e.target.checked) next.add(row.id); else next.delete(row.id); return next; })} /><span><strong>{row.title}</strong><small>{row.company_name}</small></span><span>{reasons[row.reason] || row.reason}</span></label>)}{!rows.length && <p className="learning-empty">No hay ofertas que cumplan los criterios de eliminación.</p>}<Pagination page={safePage} pages={pages} total={rows.length} pageSize={10} onChange={setPage} label="Páginas de limpieza" /><p className="text-xs text-[var(--muted)]">{data.protected}</p></>}</section>;
}
