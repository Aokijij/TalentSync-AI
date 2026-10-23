import { useState } from "react";
import { Link } from "react-router-dom";
import { Plug, RefreshCw, Search, CheckCircle2, AlertTriangle, Clock3, ArrowRight } from "lucide-react";
import { InlineNotice } from "./ui/Panel.jsx";
import { Pagination } from "./Pagination.jsx";
import "../styles/integrations.css";

const states = { local: ["Disponible localmente", "neutral"], manual: ["Gestión manual", "neutral"], disabled: ["Desactivado", "neutral"], not_configured: ["Falta configurar", "warning"], unverified: ["Sin comprobar", "warning"], observed: ["Última operación correcta", "success"], stale: ["Registro antiguo", "warning"], error: ["Requiere revisión", "error"] };
const attention = new Set(["not_configured", "unverified", "stale", "error"]);
const dateLabel = (value) => value ? new Date(value).toLocaleString("es-CO", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "Sin registros";

export function IntegrationStatus({ rows = [], onRefresh, busy = false }) {
  const [query, setQuery] = useState(""), [filter, setFilter] = useState("all"), [page, setPage] = useState(1);
  const needsReview = rows.filter((row) => attention.has(row.operational_state)).length;
  const visible = rows.filter((row) => row.name.toLocaleLowerCase("es").includes(query.toLocaleLowerCase("es").trim()) && (filter === "all" || (filter === "review" ? attention.has(row.operational_state) : ["local", "manual", "observed"].includes(row.operational_state))));
  return <section className="integration-workspace" aria-label="Estado de integraciones" aria-busy={busy}>
    <header className="integration-heading"><div><h2>Conexiones de la plataforma</h2><p>Configuración y resultados registrados. Consultar este panel no llama a los proveedores.</p></div>{onRefresh && <button type="button" className="button-secondary button-sm" disabled={busy} onClick={onRefresh}><RefreshCw size={15} />{busy ? "Actualizando…" : "Actualizar estado"}</button>}</header>
    <div className="ui-panel integration-toolbar"><div className="integration-summary"><span><strong>{rows.length}</strong> funciones e integraciones</span><span><strong>{needsReview}</strong> por revisar</span></div><div className="integration-controls"><label className="ui-filter-field"><span>Buscar integración</span><div className="integration-search"><Search size={16} aria-hidden="true" /><input type="search" className="field-control" value={query} placeholder="Nombre de la conexión" onChange={(event) => { setQuery(event.target.value); setPage(1); }} /></div></label><div className="integration-filters" aria-label="Filtrar por estado">{[["all", "Todas"], ["review", "Por revisar"], ["available", "Disponibles"]].map(([key, text]) => <button type="button" key={key} aria-pressed={filter === key} onClick={() => { setFilter(key); setPage(1); }}>{text}</button>)}</div></div></div>
    <div className="integration-grid">{visible.slice((page - 1) * 8, page * 8).map((row) => {
      const [label, tone] = states[row.operational_state] || states.unverified;
      const Icon = tone === "success" ? CheckCircle2 : ["error", "warning"].includes(tone) ? AlertTriangle : Plug;
      return <article className="ui-card integration-card" key={row.id || row.name}><header><span className="integration-symbol"><Plug size={19} /></span><h3>{row.name}</h3></header><span className="integration-state" data-tone={tone}><Icon size={14} />{label}</span><p>{row.status}</p>
        {(row.last_attempt_at || row.configured) && <dl className="integration-dates"><div><dt><Clock3 size={13} />Último intento</dt><dd>{dateLabel(row.last_attempt_at)}</dd></div><div><dt>Última operación correcta</dt><dd>{dateLabel(row.last_success_at)}</dd></div></dl>}
        {row.last_error && <InlineNotice error title="Último problema registrado">{row.last_error}</InlineNotice>}
        <details><summary>Configuración y siguiente paso</summary><dl><div><dt>Implementación</dt><dd>{row.implemented ? "Disponible" : "Pendiente"}</dd></div><div><dt>Configuración externa</dt><dd>{row.configured == null ? "No requiere proveedor" : row.configured ? "Configurada" : "Pendiente"}</dd></div></dl><p>{row.next_steps}</p>{row.action_url && <Link className="button-secondary button-sm" to={row.action_url}>{row.action_label}<ArrowRight size={14} /></Link>}</details>
      </article>;
    })}</div>
    {!visible.length && <InlineNotice title="Sin coincidencias">Prueba otro nombre o cambia el filtro de estado.</InlineNotice>}
    {visible.length > 8 && <Pagination page={page} total={visible.length} pageSize={8} onChange={setPage} label="Páginas de integraciones" busy={busy} />}
    <p className="integration-footnote">Una operación correcta puede usar caché y no garantiza disponibilidad actual. Los registros de más de 24 horas se señalan como antiguos. Un envío aceptado no confirma la entrega del correo.</p>
  </section>;
}
