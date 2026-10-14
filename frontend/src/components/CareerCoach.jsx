import { useState } from "react";
import { ArrowRight, CheckCheck, ChevronDown, Lightbulb, PencilLine } from "lucide-react";

export function CareerCoach({ guidance, onEdit, onStartWriting }) {
  const [expanded, setExpanded] = useState(false);
  if (!guidance?.items) return null;
  const shown = expanded ? guidance.items : guidance.items.slice(0, 3);
  return <section className="career-coach print-hidden" aria-labelledby="career-coach-title">
    <header><div className="career-coach-icon"><Lightbulb size={22} /></div><div><p className="career-coach-kicker">TU SIGUIENTE MEJORA</p><h2 id="career-coach-title">Haz más clara tu hoja de vida</h2><p>{guidance.total ? `${guidance.total} recomendaciones según tu último perfil guardado. Elige una para empezar.` : "No encontramos ajustes con estas reglas. Revisa también que tus datos estén actualizados."}</p></div></header>
    <div className="career-coach-list">{shown.map((item) => <article key={item.id}><div className="career-coach-item-heading"><span>{item.priority === 1 ? "Empieza aquí" : item.priority === 3 ? "Opcional" : "Para revisar"}</span><h3>{item.title}</h3></div><p>{item.detail}</p>
      {item.writing ? <button type="button" className="button-secondary button-sm" onClick={() => onStartWriting(item.experience_index)}><PencilLine size={14} />Preparar una propuesta revisable</button> : null}
      <button type="button" className="button-secondary button-sm" onClick={() => onEdit(item.target)}>Ir al campo <ArrowRight size={14} /></button>
    </article>)}</div>
    {guidance.items.length > 3 && <button type="button" className="button-secondary button-sm career-coach-more" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? "Ver menos" : `Ver las ${guidance.total} recomendaciones`}<ChevronDown size={15} /></button>}
    <footer><CheckCheck size={15} /><span>Consejos basados en tus datos y reglas de revisión. No añaden logros ni habilidades automáticamente.</span></footer>
  </section>;
}
