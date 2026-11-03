import { skillName } from "../utils/skillNames.js";
import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Clock3, ListChecks, RotateCcw, Search, SlidersHorizontal, Target, X } from "lucide-react";
import { AreaIcon } from "./LearningVisuals.jsx";
import { challengeState, latestChallengeAttempt } from "../utils/learningChallenges.js";
import { dashboardDate, timestamp } from "../utils/dashboardData.js";
import { challengeLevels, filterChallenges, levelOrder } from "../utils/challengeCatalog.js";
import { Pagination } from "./Pagination.jsx";
import "../styles/learning-catalog.css";
import "../styles/challenge-filters.css";

const emptyFilters = { query: "", level: "", sector: "", status: "" };
export function ChallengeCatalog({ assessments, areas, busy, attempt, onStart, onReview, sources = [], demandNote, focusId, now = Date.now() }) {
  const [filters, setFilters] = useState(emptyFilters), [page, setPage] = useState(1), [sort, setSort] = useState("title"), [focusedId, setFocusedId] = useState(null);
  const rows = assessments.map((row) => {
    const result = { ...row, last_attempt: latestChallengeAttempt(row, attempt) };
    return { ...result, state: challengeState(result, now) };
  }).sort((a, b) => Number(b.state.active) - Number(a.state.active)
    || (sort === "demand" ? (b.demand_count || 0) - (a.demand_count || 0) : sort === "level" ? (levelOrder[a.level] || 0) - (levelOrder[b.level] || 0) : 0)
    || a.skill.localeCompare(b.skill, "es") || (levelOrder[a.level] || 0) - (levelOrder[b.level] || 0));
  const active = rows.find((row) => row.state.active);
  const filtered = filterChallenges(focusedId ? rows.filter((row) => row.id === focusedId) : rows, filters);
  const current = Math.min(page, Math.max(1, Math.ceil(filtered.length / 12)));
  const applied = [["query", filters.query ? `Búsqueda: ${filters.query}` : ""], ["sector", filters.sector ? areas.find((row) => row.id === filters.sector)?.label || filters.sector : ""], ["level", challengeLevels[filters.level]], ["status", ({ pending: "Por completar o reforzar", passed: "Aprobados", active: "En curso" })[filters.status]]].filter(([, label]) => label);
  function change(key, value) { setFocusedId(null); setFilters((previous) => ({ ...previous, [key]: value })); setPage(1); }
  function clear() { setFocusedId(null); setFilters(emptyFilters); setPage(1); }
  useEffect(() => { if (focusId && assessments.some((row) => row.id === focusId)) { setFocusedId(focusId); setFilters(emptyFilters); setPage(1); } }, [focusId, assessments]);
  return <section className="challenge-library-v4" aria-label="Catálogo de retos">
    <header className="challenge-catalog-heading"><span className="learning-area-icon"><Target size={24} /></span><div><p className="section-kicker">DEMUESTRA LO QUE SABES</p><h2>Retos por habilidad y nivel</h2><p>Explora habilidades de distintos sectores y elige qué quieres evaluar.</p></div><span className="challenge-total"><strong>{assessments.length}</strong> retos</span></header>
    {active && <div className="challenge-resume"><Clock3 size={21} /><div><strong>Continúa tu reto</strong><p>{active.title} · El tiempo del intento sigue corriendo.</p></div><button className="button-primary button-sm" disabled={busy} onClick={() => onStart(active.id)}>Retomar intento<ArrowRight size={15} /></button></div>}
    <div className="challenge-discovery-controls">
      <header className="challenge-filter-heading"><span><SlidersHorizontal size={18} /><strong>Encuentra tu próximo reto</strong></span><p role="status"><strong>{filtered.length}</strong> de {assessments.length} retos</p></header>
      <div className="challenge-search-toolbar"><label className="challenge-search-label">Buscar retos<span><Search size={18} /><input className="field-control" placeholder="Indica la habilidad a evaluar" value={filters.query} maxLength={160} onChange={(event) => change("query", event.target.value)} /></span></label><label>Sector<select className="field-control" aria-label="Sector de los retos" value={filters.sector} onChange={(event) => change("sector", event.target.value)}><option value="">Todos los sectores</option>{areas.map((row) => <option key={row.id} value={row.id}>{row.label}</option>)}</select></label><label>Nivel<select className="field-control" aria-label="Nivel" value={filters.level} onChange={(event) => change("level", event.target.value)}><option value="">Todos los niveles</option>{Object.entries(challengeLevels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label></div>
      <div className="challenge-filter-options"><label>Mi avance<select className="field-control" aria-label="Mi avance" value={filters.status} onChange={(event) => change("status", event.target.value)}><option value="">Todos los estados</option><option value="pending">Por completar o reforzar</option><option value="passed">Aprobados</option><option value="active">En curso</option></select></label><label>Ordenar<select className="field-control" aria-label="Ordenar retos" value={sort} onChange={(event) => { setSort(event.target.value); setPage(1); }}><option value="title">Por habilidad</option><option value="level">Por nivel</option><option value="demand">Menciones en ofertas disponibles</option></select></label>{(focusedId || applied.length > 0) && <button className="button-secondary button-sm" onClick={clear}><RotateCcw size={15} />{focusedId ? "Ver todos los retos" : "Limpiar filtros"}</button>}</div>
      {(focusedId || applied.length > 0) && <div className="challenge-applied-filters" aria-label="Filtros de retos aplicados">{focusedId && <span>Seleccionado desde el curso</span>}{applied.map(([key, label]) => <button key={key} type="button" aria-label={`Quitar filtro: ${label}`} onClick={() => change(key, "")}><span>{label}</span><X size={14} /></button>)}</div>}
    </div>
    <div className="challenge-cards-v4">{filtered.slice((current - 1) * 12, current * 12).map((row) => {
      const state = row.state, title = row.title.replace(/\s*·\s*(básico|intermedio|avanzado)$/iu, "");
      return <article className={`challenge-card skill-challenge-card ${state.active ? "active" : ""} ${row.id === focusedId ? "is-focused" : ""}`} key={row.id}>
        <header><span className="learning-area-icon"><AreaIcon area={row.category} size={22} /></span><span className="challenge-sector-name">{areas.find((area) => area.id === row.category)?.label || "Habilidades profesionales"}</span><span className="challenge-level" data-level={row.level}>{challengeLevels[row.level] || "Fundamentos"}</span></header>
        <div className="skill-challenge-content"><h3>{title}</h3><p>{row.context}</p></div>
        <div className="challenge-skill-outcome"><span>Habilidad que practicarás</span><strong>{skillName(row.skill)}</strong></div>
        <div className="skill-challenge-facts"><span><Clock3 size={15} />{row.minutes} min</span><span><ListChecks size={15} />{row.question_count || 5} preguntas</span></div>
        {!!row.topics?.length && <details className="skill-challenge-topics"><summary>Contenidos del reto</summary><ul>{row.topics.map((topic) => <li key={topic}>{topic}</li>)}</ul></details>}
        {row.last_attempt && <div className={`skill-challenge-result ${state.passed ? "is-passed" : ""}`}>{state.active ? <><Clock3 size={15} />Intento en curso</> : state.completed ? <><CheckCircle2 size={15} /><span>{row.last_attempt.score}% · {state.passed ? "Aprobado" : "Por reforzar"}</span></> : <span>Intento anterior vencido</span>}</div>}
        {state.waiting && <p className="challenge-cooldown">Puedes repetir el {dashboardDate(state.retryAt)}.</p>}
        <footer><button id={`challenge-start-${row.id}`} className="button-primary challenge-card-action" disabled={busy || state.waiting || attempt?.status === "active" && attempt.assessment_id !== row.id && timestamp(attempt.expires_at) > now} onClick={() => onStart(row.id)}>{state.active ? "Continuar reto" : state.waiting ? "Disponible después" : row.last_attempt ? "Volver a intentar" : "Empezar reto"}<ArrowRight size={16} /></button>{state.completed && <button className="button-secondary button-sm" onClick={() => onReview(row.last_attempt.id)}>Ver resultado</button>}</footer>
      </article>;
    })}</div>
    {!filtered.length && <div className="learning-empty"><Target size={28} /><h3>No hay retos con estos filtros</h3><p>Prueba otra habilidad, sector o nivel.</p></div>}
    <Pagination page={current} total={filtered.length} pageSize={12} onChange={setPage} label="Páginas de retos" />
    <details className="challenge-scope"><summary>Cómo se interpreta el resultado</summary><p>Se aprueba desde el 80%. Puedes repetir después de 24 horas y la vigencia es de 180 días. Se evalúan las tareas y el nivel indicados; el resultado no sustituye experiencia ni certificaciones profesionales.</p></details>
    {!!sources.length && <details className="challenge-scope"><summary>Fuentes y selección de habilidades</summary><p>{demandNote}</p><p>La colección es editorial. Las fuentes orientan su cobertura; no son autoras ni certificadoras de los retos.</p><ul>{sources.map((source) => <li key={source.url}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title}</a><p>{source.scope}</p></li>)}</ul></details>}
  </section>;
}
