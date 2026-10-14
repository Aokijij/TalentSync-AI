import { useState } from "react";
import { ArrowRight, CheckCheck, ChevronDown, PencilLine } from "lucide-react";

export function CareerCoach({ guidance, onEdit, onStartWriting }) {
  const [expanded, setExpanded] = useState(false);
  const items = guidance?.items || [];
  const shown = expanded ? items : items.slice(0, 3);
  return <section className="career-coach" aria-labelledby="career-coach-title">
    <header><div><p className="career-coach-kicker">RECOMENDACIONES PARA TI</p><h3 id="career-coach-title">Una mejora a la vez</h3><p>{items.length ? `${items.length} recomendaciones según tu último perfil guardado. Cada una te lleva a la herramienta o al campo que necesitas.` : "No hay ajustes pendientes con estas reglas. Puedes mejorar una experiencia, preparar una versión por vacante o revisar la lectura de tu PDF."}</p></div></header>
    <div className="career-coach-list">{shown.map((item) => <article key={item.id}><div className="career-coach-item-heading"><span>{item.priority === 1 ? "Empieza aquí" : item.priority === 3 ? "Opcional" : "Para revisar"}</span><h3>{item.title}</h3></div><p>{item.detail}</p>
      <div className="career-coach-item-actions">{item.writing ? <button type="button" className="button-primary button-sm" onClick={() => onStartWriting(item.experience_index)}><PencilLine size={14} />Mejorar esta experiencia</button> : null}
      <button type="button" className="button-secondary button-sm" onClick={() => onEdit(item.target)}>{item.writing ? "Editar directamente" : "Revisar en mi perfil"} <ArrowRight size={14} /></button></div>
    </article>)}</div>
    {items.length > 3 && <button type="button" className="button-secondary button-sm career-coach-more" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? "Ver menos" : `Ver las ${items.length} recomendaciones`}<ChevronDown size={15} /></button>}
    <footer><CheckCheck size={15} /><span>Consejos basados en tus datos y reglas de revisión. No añaden logros ni habilidades automáticamente.</span></footer>
  </section>;
}
