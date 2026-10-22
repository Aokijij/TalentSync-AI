import "../styles/learning-discovery.css";
import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, Check, Search, TrendingUp } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { skillKey } from "../utils/skillLevels.js";
import { Pagination } from "./Pagination.jsx";

export function DemandSkillCard({ row, total, selected, onSelect }) {
  const share = total ? Math.min(100, Math.round(row.vacancies / total * 100)) : 0;
  return <button type="button" className="demand-skill-card" aria-pressed={selected} onClick={onSelect}>
    <span className="demand-skill-heading"><strong>{row.skill}</strong><span>{selected ? <Check size={16} /> : <ArrowRight size={16} />}</span></span>
    <span className="demand-skill-metric"><strong>{row.vacancies}</strong><span>vacantes lo solicitan</span></span>
    <span className="demand-skill-share">{share}% de la muestra · {row.companies} empresas</span><span className="demand-skill-meter" aria-hidden="true"><i style={{ width: `${share}%` }} /></span>
    <span className={`demand-skill-coverage${row.published_resources ? "" : " needs-resources"}`}><BookOpen size={14} />{row.published_resources ? `${row.published_resources} ${row.published_resources === 1 ? "recurso publicado" : "recursos publicados"}` : "Por cubrir en el catálogo"}</span>
  </button>;
}

export function LearningDemand({ selected, onSelect, onSearchSource }) {
  const [data, setData] = useState(null), [query, setQuery] = useState(""), [coverage, setCoverage] = useState("all"), [page, setPage] = useState(1), [error, setError] = useState(""), [reload, setReload] = useState(0);
  useEffect(() => { const controller = new AbortController(); setError(""); api.get("/admin/learning/demand", { signal: controller.signal }).then(({ data }) => { if (!controller.signal.aborted) setData(data); }).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure)); }); return () => controller.abort(); }, [reload]);
  const rows = (data?.skills || []).filter((row) => skillKey(row.skill).includes(skillKey(query)) && (coverage === "all" || (coverage === "published" ? row.published_resources > 0 : !row.published_resources)));
  const pages = Math.max(1, Math.ceil(rows.length / 8)), safePage = Math.min(page, pages);
  return <section className="learning-demand learning-demand-panel">
    <header className="learning-demand-header"><span className="demand-header-icon"><TrendingUp size={24} /></span><div><p className="demand-eyebrow">PLANIFICA EL CATÁLOGO</p><h2>Formación según lo que solicitan las vacantes</h2><p>Identifica las habilidades más pedidas y encuentra formación para cubrirlas.</p></div><span className="demand-sample"><strong>{data?.vacancy_sample ?? "—"}</strong><span>vacantes analizadas</span></span></header>
    <div className="demand-toolbar"><label className="demand-search"><span>Buscar habilidad</span><div><Search size={16} /><input className="field-control" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Excel, logística, Python…" /></div></label><label className="demand-coverage-filter"><span>Cobertura del catálogo</span><select className="field-control" value={coverage} onChange={(event) => { setCoverage(event.target.value); setPage(1); }}><option value="all">Todas las habilidades</option><option value="uncovered">Sin recursos publicados</option><option value="published">Con recursos publicados</option></select></label></div>
    {selected && <div className="demand-selected"><div><span>Biblioteca filtrada por</span><strong>{selected}</strong></div><button type="button" className="button-primary button-sm" onClick={() => onSearchSource(selected)}>Buscar formación<ArrowRight size={14} /></button><button type="button" className="button-secondary button-sm" onClick={() => onSelect("")}>Quitar filtro</button></div>}
    {error && <p role="alert" className="demand-error">{error}<button type="button" onClick={() => setReload((value) => value + 1)}>Reintentar</button></p>}
    {!data && !error && <p role="status" className="learning-empty">Consultando las habilidades de las vacantes activas…</p>}
    {data && <><div className="demand-results-heading"><h3>Habilidades más solicitadas</h3><span>{rows.length} {rows.length === 1 ? "habilidad" : "habilidades"}{coverage === "uncovered" ? " por cubrir" : ""}</span></div><div className="demand-skills-grid">{rows.slice((safePage - 1) * 8, safePage * 8).map((row) => <DemandSkillCard key={row.skill} row={row} total={data.vacancy_sample} selected={selected === row.skill} onSelect={() => onSelect(selected === row.skill ? "" : row.skill)} />)}</div>
    {!rows.length && <p className="learning-empty">No hay habilidades con estos filtros. Prueba otra búsqueda o cambia la cobertura.</p>}
    <footer className="demand-pagination"><Pagination page={safePage} pages={pages} total={rows.length} pageSize={8} onChange={setPage} label="Habilidades solicitadas" /></footer><p className="demand-footnote">{data.notice}</p></>}
  </section>;
}
