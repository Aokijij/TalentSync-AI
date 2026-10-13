import { useState } from "react";
import { ArrowRight, CheckCheck, ChevronDown, Lightbulb, PencilLine } from "lucide-react";
import { buildStarDraft } from "../utils/careerCoach.js";

export function CareerCoach({ guidance, profile, onEdit, onApply }) {
  const [expanded, setExpanded] = useState(false);
  if (!guidance?.items) return null;
  const shown = expanded ? guidance.items : guidance.items.slice(0, 3);
  return <section className="career-coach print-hidden" aria-labelledby="career-coach-title">
    <header><div className="career-coach-icon"><Lightbulb size={22} /></div><div><p className="career-coach-kicker">TU SIGUIENTE MEJORA</p><h2 id="career-coach-title">Haz más clara tu hoja de vida</h2><p>{guidance.total ? `${guidance.total} recomendaciones según tu último perfil guardado. Elige una para empezar.` : "No encontramos ajustes con estas reglas. Revisa también que tus datos estén actualizados."}</p></div></header>
    <div className="career-coach-list">{shown.map((item) => <article key={item.id}><div className="career-coach-item-heading"><span>{item.priority === 1 ? "Empieza aquí" : item.priority === 3 ? "Opcional" : "Para revisar"}</span><h3>{item.title}</h3></div><p>{item.detail}</p>
      {item.writing ? <StarAssistant key={`${item.id}-${item.original}`} item={item} profile={profile} onApply={onApply} /> : null}
      <button type="button" className="button-secondary button-sm" onClick={() => onEdit(item.target)}>Ir al campo <ArrowRight size={14} /></button>
    </article>)}</div>
    {guidance.items.length > 3 && <button type="button" className="button-secondary button-sm career-coach-more" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? "Ver menos" : `Ver las ${guidance.total} recomendaciones`}<ChevronDown size={15} /></button>}
    <footer><CheckCheck size={15} /><span>Consejos basados en tus datos y reglas de revisión. No añaden logros ni habilidades automáticamente.</span></footer>
  </section>;
}

function StarAssistant({ item, profile, onApply }) {
  const [facts, setFacts] = useState({ situation: "", task: "", action: "", result: "" });
  const [applied, setApplied] = useState(false);
  const draft = buildStarDraft(facts);
  const original = profile.experiences[item.experience_index]?.description || "";
  const unchanged = original.trim() === (item.original || "").trim();
  const fields = [["situation", "Situación", "¿Qué problema o necesidad había?"], ["task", "Objetivo", "¿Qué tenías que conseguir?"], ["action", "Tu acción", "¿Qué hiciste tú y con qué herramienta o método?"], ["result", "Resultado real", "¿Qué cambió o qué entregaste? Usa cifras solo si puedes respaldarlas."]];
  return <details className="career-star"><summary><PencilLine size={15} /> Preparar una redacción con mis datos</summary>
    {item.original && <blockquote><strong>Texto guardado</strong>{item.original}</blockquote>}
    <p>Completa estos cuatro puntos con hechos de esa experiencia. La vista previa une tus respuestas; puedes editarlas antes de aplicarlas.</p>
    <div className="career-star-fields">{fields.map(([key, label, placeholder]) => <label key={key}>{label}<textarea rows={2} maxLength={700} value={facts[key]} placeholder={placeholder} onChange={(event) => { setFacts((current) => ({ ...current, [key]: event.target.value })); setApplied(false); }} /></label>)}</div>
    {draft && <div className="career-star-preview"><strong>Vista previa del borrador</strong><p>{draft}</p></div>}
    {!unchanged && !applied && <p role="status">La descripción cambió. Guarda el perfil para recalcular la recomendación antes de aplicar este borrador.</p>}
    <button type="button" className="button-primary button-sm" disabled={!draft || !unchanged || applied} onClick={() => { onApply(item.experience_index, draft); setApplied(true); }}>{applied ? "Añadido al borrador" : "Usar en el borrador de esta experiencia"}</button>
    {applied && <p role="status">Revisa la experiencia y pulsa Guardar en tu perfil para conservar el cambio.</p>}
  </details>;
}
