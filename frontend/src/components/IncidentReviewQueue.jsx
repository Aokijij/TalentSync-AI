import { useEffect, useRef, useState } from "react";
import { ArrowRight, ClipboardList, Clock3, RefreshCw, Search, X } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { IncidentCard } from "./IncidentCard.jsx";
import { Pagination } from "./Pagination.jsx";

const STATES = { open: "Recibida", in_review: "En revisión", appealed: "Apelación pendiente", confirmed: "Confirmada", dismissed: "Desestimada" };
const CATEGORIES = { ghosting: "Falta de respuesta", inappropriate_interview: "Entrevista inapropiada", suspected_fraud: "Posible fraude", discrimination: "Posible discriminación", other: "Otra situación" };
const PAGE_SIZE = 8;
const date = (value) => value ? new Date(value.endsWith("Z") ? value : `${value}Z`).toLocaleDateString("es-CO") : "Sin fecha";

export function IncidentReviewQueue({ onReviewed }) {
  const [bucket, setBucket] = useState("pending"), [status, setStatus] = useState("all"), [category, setCategory] = useState("all");
  const [search, setSearch] = useState(""), [query, setQuery] = useState(""), [sort, setSort] = useState("priority"), [page, setPage] = useState(1);
  const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0), [selected, setSelected] = useState(null), [message, setMessage] = useState("");
  useEffect(() => { const timer = window.setTimeout(() => { setQuery(search.trim()); setPage(1); }, 300); return () => window.clearTimeout(timer); }, [search]);
  useEffect(() => {
    let active = true;
    setLoading(true); setError("");
    api.get("/admin/incident-queue", { params: { bucket, status, category, search: query, sort, page, page_size: PAGE_SIZE } }).then(({ data: result }) => { if (active) setData(result); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [bucket, status, category, query, sort, page, refresh]);
  const counts = data?.counts || {};
  const pending = (counts.open || 0) + (counts.in_review || 0) + (counts.appealed || 0);
  const resolved = (counts.confirmed || 0) + (counts.dismissed || 0);
  const waiting = loading || search.trim() !== query;
  function changeBucket(value) { setBucket(value); setStatus("all"); setPage(1); }
  function clearFilters() { setSearch(""); setQuery(""); setStatus("all"); setCategory("all"); setPage(1); }
  return <section className="surface-card incident-inbox" aria-labelledby="incident-inbox-title">
    <header className="incident-inbox-header"><div className="incident-inbox-heading"><span><ClipboardList size={23} /></span><div><h2 id="incident-inbox-title">Bandeja de incidencias</h2><p>Prioriza solicitudes y abre un caso para revisar sus hechos y responder.</p></div></div><button type="button" className="button-secondary button-sm" disabled={waiting} onClick={() => setRefresh((value) => value + 1)}><RefreshCw size={15} />Actualizar</button></header>
    <div className="incident-inbox-summary"><span><Clock3 size={15} /><strong>{pending}</strong> {pending === 1 ? "pendiente" : "pendientes"}</span><span><strong>{counts.appealed || 0}</strong> {counts.appealed === 1 ? "apelación pendiente" : "apelaciones pendientes"}</span><span><strong>{resolved}</strong> {resolved === 1 ? "resuelta" : "resueltas"}</span></div>
    <nav className="incident-inbox-tabs" aria-label="Bandejas de incidencias">{[["pending", "Pendientes", pending], ["resolved", "Resueltas", resolved], ["all", "Todas", pending + resolved]].map(([value, label, count]) => <button type="button" key={value} aria-pressed={bucket === value} onClick={() => changeBucket(value)}>{label}<span>{count}</span></button>)}</nav>
    <div className="incident-inbox-filters"><label className="incident-inbox-search"><Search size={17} /><input className="field-control" aria-label="Buscar incidencias" maxLength={120} placeholder="Empresa, vacante o número de caso" value={search} onChange={(event) => setSearch(event.target.value)} /></label><select className="field-control" aria-label="Estado de la incidencia" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="all">Todos los estados</option>{Object.entries(STATES).filter(([key]) => bucket === "all" || (bucket === "pending" ? ["open", "in_review", "appealed"].includes(key) : ["confirmed", "dismissed"].includes(key))).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select className="field-control" aria-label="Tipo de incidencia" value={category} onChange={(event) => { setCategory(event.target.value); setPage(1); }}><option value="all">Todos los tipos</option>{Object.entries(CATEGORIES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
    <div className="incident-inbox-order"><p>{waiting ? "Cargando solicitudes…" : `${data?.total || 0} ${data?.total === 1 ? "caso" : "casos"} en esta bandeja`}</p><label>Ordenar<select aria-label="Ordenar incidencias" value={sort} onChange={(event) => { setSort(event.target.value); setPage(1); }}><option value="priority">Apelaciones primero</option><option value="oldest">Más antiguas</option><option value="newest">Más recientes</option></select></label></div>
    {message && <p role="status" className="incident-inbox-message">{message}</p>}
    {error ? <div role="alert" className="incident-inbox-empty"><p>{error}</p><button type="button" className="button-secondary" onClick={() => setRefresh((value) => value + 1)}>Reintentar</button></div> : <div className="incident-inbox-list" aria-busy={waiting}>
      {!data && loading && <p className="incident-inbox-empty">Cargando la bandeja…</p>}
      {data?.items.map((row) => <article className={`incident-inbox-row state-${row.status}`} key={row.id}><span className="incident-inbox-id">#{row.id}</span><div className="incident-inbox-identity"><h3>{row.company_name}</h3><p>{row.job_title || "Proceso no disponible"}</p><small>{CATEGORIES[row.category] || row.category}</small></div><div className="incident-inbox-meta"><span className="incident-status">{STATES[row.status]}</span><time dateTime={row.created_at}>Registrada {date(row.created_at)}</time></div><button type="button" className="button-secondary button-sm" disabled={waiting} aria-label={`Revisar caso ${row.id}`} onClick={() => { setSelected(row); setMessage(""); }}>Revisar<ArrowRight size={15} /></button></article>)}
      {data && !data.items.length && !waiting && <div className="incident-inbox-empty"><ClipboardList size={30} /><h3>{query || status !== "all" || category !== "all" ? "No hay coincidencias" : bucket === "pending" ? "Sin solicitudes pendientes" : "Esta bandeja está vacía"}</h3><p>{query || status !== "all" || category !== "all" ? "Prueba con otro dato o limpia los filtros." : "Los casos que correspondan aparecerán aquí."}</p>{(query || status !== "all" || category !== "all") && <button type="button" className="button-secondary button-sm" onClick={clearFilters}>Limpiar filtros</button>}</div>}
    </div>}
    {data && !error && <div className={waiting ? "incident-inbox-pagination is-loading" : "incident-inbox-pagination"}><Pagination page={data.page} pages={Math.max(1, Math.ceil(data.total / PAGE_SIZE))} total={data.total} pageSize={PAGE_SIZE} onChange={setPage} label="Paginación de incidencias" /></div>}
    <p className="incident-inbox-footnote">{sort === "priority" ? "Apelaciones primero; después, solicitudes recibidas y revisiones en curso, de la más antigua a la más reciente." : sort === "oldest" ? "Casos ordenados por fecha de registro, de la más antigua a la más reciente." : "Casos ordenados por fecha de registro, de la más reciente a la más antigua."} Una solicitud pendiente no modifica la valoración de la empresa.</p>
    {selected && <IncidentReviewDialog key={selected.id} selected={selected} onClose={() => setSelected(null)} onSaved={(id) => { setSelected(null); setMessage(`Decisión del caso #${id} guardada. Se notificó a ambas partes.`); setRefresh((value) => value + 1); onReviewed?.(); }} />}
  </section>;
}

function IncidentReviewDialog({ selected, onClose, onSaved }) {
  const dialog = useRef(null), closeButton = useRef(null), errorElement = useRef(null);
  const [incident, setIncident] = useState(null), [error, setError] = useState(""), [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [retry, setRetry] = useState(0);
  useEffect(() => { const modal = dialog.current; modal.showModal(); closeButton.current?.focus(); return () => modal.close(); }, []);
  useEffect(() => { if (error) errorElement.current?.scrollIntoView({ block: "center" }); }, [error]);
  useEffect(() => {
    let active = true; setLoading(true); setError("");
    api.get(`/admin/incidents/${selected.id}`).then(({ data }) => { if (active) setIncident(data); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [selected.id, retry]);
  async function save(event) {
    event.preventDefault(); const payload = Object.fromEntries(new FormData(event.currentTarget));
    setBusy(true); setError("");
    try { await api.patch(`/admin/incidents/${selected.id}`, payload); onSaved(selected.id); }
    catch (failure) { setError(getApiErrorMessage(failure)); setBusy(false); }
  }
  return <dialog ref={dialog} className="incident-review-dialog" aria-labelledby="incident-dialog-title" onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }} onClick={(event) => { if (event.target === event.currentTarget && !busy) { const box = event.currentTarget.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) onClose(); } }}>
    <header className="incident-review-dialog-header"><div><p className="section-kicker">Revisión individual</p><h2 id="incident-dialog-title">Caso #{selected.id}</h2></div><button ref={closeButton} type="button" className="button-secondary button-sm" aria-label="Cerrar revisión de incidencia" disabled={busy} onClick={onClose}><X size={18} /></button></header>
    <div className="incident-review-dialog-content">
      {loading && <p role="status">Cargando detalle del caso…</p>}
      {error && <p ref={errorElement} role="alert" className="incident-review-error">{error}</p>}
      {!loading && !incident && <button type="button" className="button-secondary" onClick={() => setRetry((value) => value + 1)}>Reintentar</button>}
      {incident && <><IncidentCard incident={incident} expanded /><form className="incident-decision-form" onSubmit={save}><h3>Registrar una decisión</h3><p>El resumen será compartido con la persona que reportó y la empresa. Explica los hechos revisados y el motivo de la decisión.</p><fieldset disabled={busy}><label>Decisión<select className="field-control" name="status" defaultValue="" required><option value="" disabled>Selecciona una decisión</option><option value="in_review">Continuar en revisión</option><option value="confirmed">Confirmar hechos revisados</option><option value="dismissed">Desestimar</option></select></label><label>Resumen para ambas partes<textarea className="field-control" name="shared_summary" minLength={10} maxLength={1500} rows={4} required defaultValue={incident.shared_summary || ""} /></label></fieldset><footer><button type="button" className="button-secondary" disabled={busy} onClick={onClose}>Cerrar sin guardar</button><button className="button-primary" disabled={busy}>{busy ? "Guardando…" : "Guardar decisión motivada"}</button></footer></form></>}
    </div>
  </dialog>;
}
