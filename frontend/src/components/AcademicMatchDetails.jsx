import { Check, CircleHelp, GraduationCap, Minus, X } from "lucide-react";
import { academicPresentation } from "../utils/academicPresentation.js";

export function AcademicMatchDetails({ value }) {
  if (!value || value.status === "not_required") return null;
  const presentation = academicPresentation(value);
  return <section className={`academic-match academic-comparison ${presentation.tone}`} aria-label="Comparación de formación">
    <header><span className="academic-heading-icon"><GraduationCap size={21} /></span><div><h3>{presentation.title}</h3><p>{presentation.summary}</p></div></header>
    <div className="academic-checks">{presentation.checks.map((check) => { const Icon = check.tone === "met" ? Check : check.tone === "unmet" ? X : check.tone === "partial" ? Minus : CircleHelp; return <article key={check.key} className={`academic-check ${check.tone}`}><div className="academic-check-heading"><h4>{check.label}</h4><span><Icon size={14} />{check.result}</span></div><dl><div><dt>La oferta solicita</dt><dd>{check.requested}</dd></div><div><dt>Formación registrada</dt><dd>{check.actual}</dd></div></dl><p>{check.explanation}</p></article>; })}</div>
    <footer>Se compara el mismo estudio en los tres puntos. Esta información es declarada; el diploma no se verifica automáticamente.</footer>
  </section>;
}
