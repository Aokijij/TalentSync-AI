import { useState } from "react";
import { Award, ArrowRight, ArrowUpRight, BookOpenCheck, CalendarDays, ClipboardCheck, FlaskConical } from "lucide-react";
import { Link } from "react-router-dom";
import { WorkspaceTabs } from "./ui/Panel.jsx";
import { Pagination } from "./Pagination.jsx";
import "../styles/learning-revision.css";
import { challengeLevels } from "../utils/challengeCatalog.js";

const keyText = (value) => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
function dateText(value) { if (!value) return "Fecha sin registrar"; const text = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`; const time = Date.parse(text); return Number.isFinite(time) ? new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", year: "numeric", timeZone: "America/Bogota" }).format(time) : "Fecha sin registrar"; }
export function LearningResults({ passport, onReview, plans = [], onOpenPractice }) {
  const practices = passport.learning_results || [], courses = passport.course_results || [], certificates = passport.certificates || [], assessments = passport.assessments || [];
  const groups = { practices, courses, certificates, assessments };
  const [tab, setTab] = useState(practices.length ? "practices" : assessments.length ? "assessments" : courses.length ? "courses" : certificates.length ? "certificates" : "practices");
  const [query, setQuery] = useState(""), [page, setPage] = useState(1);
  const rows = groups[tab].filter((row) => keyText([row.title, row.name, row.provider, row.issuer, row.skill, ...(row.skills || [])].join(" ")).includes(keyText(query.trim())));
  const pages = Math.max(1, Math.ceil(rows.length / 8)), safePage = Math.min(page, pages);
  return <section className="learning-results-v2 space-y-5" aria-label="Resultados de aprendizaje">
    <header className="results-page-heading"><div><p className="section-kicker">TU PROGRESO, CON CONTEXTO</p><h2>Mis resultados</h2><p>Cada actividad conserva su alcance: práctica, formación terminada por ti, documento aportado o reto de habilidades.</p></div><Link className="button-secondary button-sm" to="/perfil#evidencias">Ver mi perfil<ArrowUpRight size={15} /></Link></header>
    <WorkspaceTabs id="learning-results" label="Tipos de resultados" value={tab} onChange={(value) => { setTab(value); setPage(1); }} items={[["practices", `Prácticas (${practices.length})`, FlaskConical], ["courses", `Cursos (${courses.length})`, BookOpenCheck], ["certificates", `Certificados (${certificates.length})`, Award], ["assessments", `Retos (${assessments.length})`, ClipboardCheck]]} />
    <div role="tabpanel" id={`learning-results-panel-${tab}`} aria-labelledby={`learning-results-tab-${tab}`}>
      <div className="results-toolbar"><label>Buscar en mis resultados<input className="field-control mt-2" value={query} maxLength={160} placeholder="Busca por recurso, habilidad o emisor" onChange={(event) => { setQuery(event.target.value); setPage(1); }} /></label><p>{rows.length} {rows.length === 1 ? "registro" : "registros"}</p></div>
      <p className="results-kind-description">{({ practices: "La puntuación corresponde al ejercicio de TalentSync, no a la finalización del curso ni a un certificado del proveedor.", courses: "Formación que marcaste como finalizada. El avance es una declaración tuya y no incluye una nota de práctica.", certificates: "Documentos aportados por ti. TalentSync no valida su autenticidad ni los convierte en evaluaciones de habilidades.", assessments: "Cada resultado corresponde al nivel y las actividades indicadas. Revisa su fecha de vigencia y alcance." })[tab]}</p>
      <div className="results-record-grid">{rows.slice((safePage - 1) * 8, safePage * 8).map((row, index) => {
        const isPractice = tab === "practices", isAssessment = tab === "assessments", score = (isPractice || isAssessment) && row.score != null ? Number(row.score) : null;
        const plan = plans.find((item) => item.resource?.id === row.resource_id);
        const title = row.title || row.name || `Fundamentos de ${row.skill || "la habilidad"}`;
        const status = tab === "certificates" ? "Aportado por ti" : tab === "courses" ? "Finalizado por ti" : isAssessment ? row.valid ? "Vigente" : row.passed ? "Por renovar" : "Por reforzar" : row.published ? "Evidencia declarada publicada" : "Resultado personal";
        return <article className="result-record" key={row.id || `${tab}-${row.resource_id || index}`}>
          <header><span className={`result-record-status ${row.valid || row.passed ? "is-positive" : ""}`}>{status}</span>{score != null && Number.isFinite(score) && <strong className="result-record-score">{score}<small>%</small></strong>}</header>
          <h3>{title}</h3>
          <p className="result-record-context">{isPractice ? row.course_title ? `Curso relacionado: ${row.course_title}` : row.provider && row.provider !== "TalentSync" ? "Registro anterior de práctica asociado a formación" : "Práctica de TalentSync" : row.provider || row.issuer || row.skill}</p>
          <div className="result-record-meta">{isAssessment && <span>{challengeLevels[row.level] || "Fundamentos"}</span>}{isPractice && <span>Intento {row.attempt_number || 1}</span>}<span><CalendarDays size={14} />{tab === "certificates" ? row.year || "Año sin registrar" : isAssessment && row.passed && row.valid_until ? `${row.valid ? "Vigente hasta" : "Venció"} ${dateText(row.valid_until)}` : dateText(row.completed_at || row.started_at)}</span></div>
          {score != null && Number.isFinite(score) && <div className="result-record-track" aria-hidden="true"><span style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></div>}
          {isPractice && !!row.feedback?.length && <details className="result-record-feedback"><summary>Ver correcciones ({row.feedback.length})</summary>{row.feedback.map((item) => <div key={item.question_id}><strong>{item.correct ? "Bien resuelto" : "Por reforzar"}</strong><p>{item.prompt}</p><small>{item.message}</small></div>)}</details>}
          <footer>{isAssessment ? <button className="button-primary button-sm" onClick={() => onReview(row)}>Ver resultado y correcciones<ArrowRight size={15} /></button> : tab === "certificates" && row.url?.startsWith("https://") ? <a className="button-secondary button-sm" href={row.url} target="_blank" rel="noopener noreferrer">Ver documento<ArrowUpRight size={14} /></a> : plan ? <button className="button-secondary button-sm" onClick={() => onOpenPractice(row.resource_id)}>Abrir en Mi plan<ArrowUpRight size={14} /></button> : <span className="text-xs text-[var(--muted)]">Registro conservado en tu historial</span>}</footer>
        </article>;
      })}</div>
      {!rows.length && <div className="learning-empty"><BookOpenCheck size={28} /><h3>{query ? "No hay resultados con esta búsqueda" : "Todavía no hay registros en esta sección"}</h3><p>{query ? "Prueba otro recurso, habilidad o emisor." : "Tu actividad aparecerá aquí cuando la registres. Puedes seguir aprendiendo a tu ritmo."}</p></div>}
      <Pagination page={safePage} pages={pages} total={rows.length} pageSize={8} onChange={setPage} label="Páginas de mis resultados" />
    </div>
    {!!passport.practice_evidence?.length && !practices.length && <aside className="results-scope-note"><strong>También tienes trabajos publicados en tu perfil</strong><p>Son evidencias declaradas y se consultan aparte de las evaluaciones.</p><Link className="button-secondary button-sm" to="/perfil#evidencias">Ver evidencias<ArrowUpRight size={14} /></Link></aside>}
    <details className="result-scope"><summary>Qué significan estos resultados</summary><p className="mt-2">{passport.notice}</p></details>
  </section>;
}
