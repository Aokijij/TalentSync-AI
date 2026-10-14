import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, BookOpen, X, ScanText, Undo2 } from "lucide-react";
import { getApiErrorMessage } from "../api/client.js";
import { pendingCvMentions, skillKey, skillName } from "../utils/skillNames.js";

const labels = { learning: "Mencionada como aprendizaje", negated: "El texto indica falta de experiencia", project: "Mencionada en un proyecto", training: "Mencionada en formación", unknown: "Falta confirmar el contexto" };
export function CvContextReview({ rows = [], skills = [], decisions = {}, disabled, onDecision }) {
  const [busy, setBusy] = useState(""), [message, setMessage] = useState(""), [error, setError] = useState("");
  const unique = [...new Map(rows.filter((row) => labels[row.state]).map((row) => [skillKey(row.skill), row])).values()];
  const review = pendingCvMentions(unique, skills, decisions);
  const dismissed = unique.filter((row) => decisions[skillKey(row.skill)] === "dismissed");
  async function decide(skill, action) {
    setBusy(skill); setError("");
    try { await onDecision(skill, action); setMessage(action === "confirm" ? `${skill} se añadió a tus habilidades declaradas.` : action === "dismiss" ? "Mención descartada. Puedes recuperarla abajo." : "Mención recuperada para revisar."); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(""); }
  }
  if (!review.length && !dismissed.length && !message) return null;
  return <section className="cv-mentions"><header><ScanText size={19} /><div><h3>Completa tus habilidades</h3><p>{review.length ? `${review.length} menciones de tu CV por revisar` : "Has revisado las menciones disponibles"}</p></div></header>
    <p>Elige solo las que realmente conoces. Confirmarlas las añade a tu perfil como habilidades declaradas.</p>
    {disabled && <p className="cv-mention-notice">Guarda tus cambios del perfil para confirmar o descartar menciones.</p>}
    {message && <p role="status" className="cv-mention-notice">{message}</p>}{error && <p role="alert" className="text-[var(--error)]">{error}</p>}
    {review.map((row) => <article key={row.skill}><div className="cv-mention-heading"><strong>{skillName(row.skill)}</strong><span>{labels[row.state]}</span></div><details><summary>Ver dónde aparece en mi CV</summary><blockquote>{row.excerpt}</blockquote><p>{row.reason}</p></details>
      <div className="cv-mention-actions"><button type="button" className="cv-confirm-button" disabled={disabled || !!busy} onClick={() => decide(row.skill, "confirm")}><Check size={15} />{busy === row.skill ? "Guardando…" : "Añadir a mis habilidades"}</button><Link to={`/aprendizaje?search=${encodeURIComponent(row.skill)}#cursos`}><BookOpen size={15} />Ver formación</Link><button type="button" disabled={disabled || !!busy} onClick={() => decide(row.skill, "dismiss")} aria-label={`Descartar mención de ${row.skill}`}><X size={15} />Descartar</button></div>
    </article>)}
    {!!dismissed.length && <details className="cv-dismissed"><summary>Descartadas ({dismissed.length})</summary>{dismissed.map((row) => <div key={row.skill}><span>{row.skill}</span><button type="button" disabled={disabled || !!busy} onClick={() => decide(row.skill, "restore")}><Undo2 size={14} />Recuperar</button></div>)}</details>}
  </section>;
}
