import { useState } from "react";
import { Building2, ChevronDown } from "lucide-react";
import { TrustCard } from "./TrustCard.jsx";
import { Pagination } from "./Pagination.jsx";
import { useDebouncedValue, usePagedList } from "../hooks/usePagedList.js";

export function CompanyTrustDirectory({ refresh = 0 }) {
  const [query, setQuery] = useState(""), [filter, setFilter] = useState("all"), [page, setPage] = useState(1), [selected, setSelected] = useState(null);
  const search = useDebouncedValue(query);
  const { data, loading, error, reload } = usePagedList("/admin/company-directory", { search, filter, page, page_size: 6 }, refresh);
  const rows = data?.items || [], waiting = loading || search !== query.trim();
  const total = data?.total || 0, pages = Math.max(1, Math.ceil(total / 6)), safePage = data?.page || 1;
  function changePage(next) { setPage(next); setSelected(null); }
  return <section className="surface-card p-5 space-y-4">
    <header className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="flex items-center gap-2 text-lg font-bold"><Building2 size={20} />Comportamiento de las empresas</h2><p className="mt-1 text-xs text-[var(--muted)]">Consulta una empresa para ver sus métricas e historial de valoración.</p></div><span className="status-chip">{data?.organization_count || 0} organizaciones</span></header>
    <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm">Buscar empresa<input className="field-control mt-1" maxLength={120} value={query} placeholder="Nombre de la empresa" onChange={(event) => { setQuery(event.target.value); changePage(1); }} /></label><label className="text-sm">Comportamiento<select className="field-control mt-1" value={filter} onChange={(event) => { setFilter(event.target.value); changePage(1); }}><option value="all">Todas las empresas</option><option value="attention">Con incidencias o plazos vencidos</option><option value="rated">Con valoración</option><option value="unrated">Sin valoración suficiente</option></select></label></div>
    {waiting && <p role="status" className="text-sm text-[var(--muted)]">Cargando empresas…</p>}{error && <p role="alert" className="offer-alert error">{error}<button type="button" className="button-secondary button-sm" onClick={reload}>Reintentar</button></p>}
    <div className="trust-directory" aria-busy={waiting}>{rows.map((row) => <div key={row.id} className="trust-directory-entry"><button className="trust-directory-row" disabled={waiting} aria-expanded={selected === row.id} onClick={() => setSelected(selected === row.id ? null : row.id)}><span className="min-w-0"><strong>{row.company_name || row.name}</strong><small>{row.visibility_reduced ? "Requiere atención" : "Visibilidad normal"}</small></span><span><b>{row.score != null ? `${row.score}/100` : "Sin valoración"}</b><small>{row.measured_processes} procesos · {row.confirmed_incidents} incidencias</small></span><ChevronDown size={17} className={selected === row.id ? "rotate-180" : ""} /></button>{selected === row.id && <div className="p-3"><TrustCard data={row} /></div>}</div>)}{!waiting && !error && !rows.length && <p className="p-6 text-center text-sm text-[var(--muted)]">No hay empresas con estos filtros.</p>}</div>
    <Pagination page={safePage} pages={pages} total={total} pageSize={6} onChange={(next) => { if (!waiting) changePage(next); }} label="Paginación del comportamiento de empresas" />
  </section>;
}
