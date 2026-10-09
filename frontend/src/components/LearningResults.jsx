import { Award, ArrowUpRight, BookOpenCheck, CalendarDays, Clock3, RotateCcw } from "lucide-react";
import { Link } from "react-router-dom";

export function LearningResults({ passport, onReview }) {
  const results = passport.assessments || [];
  const valid = results.filter((row) => row.valid).length;
  return <section className="space-y-5" aria-label="Resultados de aprendizaje">
    <header className="flex flex-wrap items-end justify-between gap-3"><div><p className="section-kicker">Tu progreso, con evidencia</p><h2 className="mt-2 text-2xl font-bold">Lo que has demostrado</h2><p className="mt-2 text-sm text-[var(--muted)]">Revisa tus logros y elige tu siguiente paso.</p></div><Link className="button-secondary button-sm" to="/perfil#evidencias">Ver mi perfil<ArrowUpRight size={15} /></Link></header>
    <div className="results-summary"><div><Award size={22} /><strong>{valid}</strong><span>Resultados vigentes</span></div><div><BookOpenCheck size={22} /><strong>{passport.practice_evidence?.length || 0}</strong><span>Trabajos publicados</span></div><div><RotateCcw size={22} /><strong>{results.length - valid}</strong><span>Para repasar o renovar</span></div></div>
    {!results.length && <div className="learning-empty"><Award size={32} /><h3 className="font-bold">Tu primer logro empieza con un reto</h3><p>Al entregar verás el resultado, las correcciones y qué practicar después.</p></div>}
    <div className="results-grid">{results.map((row) => { const state = row.valid ? "valid" : row.passed ? "expired" : "practice"; return <article className={`result-card ${state}`} key={row.id}>
      <div className="result-score" style={{ "--result-score": `${row.score}%` }}><strong>{row.score}<small>%</small></strong></div><div className="min-w-0 flex-1"><span className="result-badge">{row.valid ? "Vigente" : row.passed ? "Por renovar" : "Por reforzar"}</span><h3 className="mt-3 text-lg font-bold">{row.skill.toUpperCase()}</h3>{row.title && row.title.toLowerCase() !== row.skill.toLowerCase() && <p className="mt-1 text-sm font-semibold">{row.title}</p>}<p className="mt-1 text-sm text-[var(--muted)]">{row.valid ? "Fundamentos acreditados" : row.passed ? "Aprobaste; renueva su vigencia" : "Retoma la práctica y vuelve a intentarlo"}</p><p className="mt-3 flex items-center gap-2 text-xs text-[var(--muted)]">{row.valid ? <CalendarDays size={14} /> : <Clock3 size={14} />}{row.valid_until && row.passed ? `${row.valid ? "Válido hasta" : "Venció el"} ${new Date(row.valid_until + "Z").toLocaleDateString("es-CO")}` : "Correcciones y recursos disponibles"}</p><button className="result-review" onClick={() => onReview(row)}>Ver resultado y próximos pasos<ArrowUpRight size={16} /></button></div></article>; })}</div>
    <details className="result-scope"><summary>Qué significan estos resultados</summary><p className="mt-2">{passport.notice}</p></details>
  </section>;
}
