import { AutoResizeTextarea } from "./AutoResizeTextarea.jsx";
import { AddItemButton } from "./AddItemButton.jsx";
import { MessageSquarePlus, Trash2 } from "lucide-react";

export function ScreeningQuestionsEditor({ value, onChange }) {
  const update = (index, changes) =>
    onChange(value.map((question, position) => position === index ? { ...question, ...changes } : question));
  const remove = (index) => onChange(value.filter((_, position) => position !== index));
  const add = () =>
    onChange([
      ...value,
      {
        id: `question_${Date.now()}`,
        prompt: "",
        type: "open",
        required: true,
        options: [],
        option_scores: {},
      },
    ]);
  return <section className="screening-editor"><header><h3>Preguntas antes de postularse</h3><p>Añade solo preguntas relevantes para el cargo. Puedes solicitar una respuesta abierta o presentar opciones con una valoración definida.</p></header><div className="screening-list">{value.map((question, index) => <article key={question.id} className="screening-question"><header><span>{index + 1}</span><strong>Pregunta {index + 1}</strong><button type="button" className="button-ghost button-sm" onClick={() => remove(index)} aria-label={`Eliminar pregunta ${index + 1}`}><Trash2 size={16} /></button></header><label className="screening-prompt">¿Qué quieres preguntar?<AutoResizeTextarea rows={3} value={question.prompt} maxLength={300} placeholder="Ej. Describe una situación en la que hayas aplicado estos conocimientos." onChange={(event) => update(index, { prompt: event.target.value })} /><small>{question.prompt.length}/300 caracteres</small></label><div className="screening-settings"><label>Tipo de respuesta<select className="field-control" value={question.type} onChange={(event) => update(index, { type: event.target.value, options: [], option_scores: {} })}><option value="open">Respuesta abierta</option><option value="choice">Elegir una opción</option></select></label><label className="screening-required"><input type="checkbox" checked={question.required ?? true} onChange={(event) => update(index, { required: event.target.checked })} />Respuesta obligatoria</label></div>{question.type === "choice" ? <ChoiceOptions question={question} onChange={(changes) => update(index, changes)} /> : <p className="screening-hint">Tu equipo revisará la respuesta completa. Esta pregunta no cambia automáticamente la compatibilidad.</p>}</article>)}{!value.length && <p className="screening-empty">Las preguntas son opcionales. Añádelas si te ayudan a conocer mejor a quienes se postulan.</p>}</div><AddItemButton icon={MessageSquarePlus} help={`${value.length}/10 preguntas · Abiertas o con opciones de respuesta`} disabled={value.length >= 10} onClick={add}>Añadir pregunta</AddItemButton></section>;
}

function ChoiceOptions({ question, onChange }) {
  const options = question.options || [];
  const rename = (position, label) => {
    const previous = options[position];
    const nextOptions = options.map((option, index) => index === position ? label : option);
    const nextScores = { ...(question.option_scores || {}) };
    const score = Number(nextScores[previous] || 0);
    delete nextScores[previous];
    if (label.trim()) nextScores[label] = score;
    onChange({ options: nextOptions, option_scores: nextScores });
  };
  const setScore = (option, score) => onChange({ option_scores: { ...(question.option_scores || {}), [option]: Number(score) } });
  const removeOption = (position) => {
    const removed = options[position];
    const nextOptions = options.filter((_, index) => index !== position);
    const nextScores = { ...(question.option_scores || {}) };
    delete nextScores[removed];
    onChange({ options: nextOptions, option_scores: nextScores });
  };
  return <div className="screening-options"><header><h4>Opciones de respuesta</h4><p>Escribe cada opción completa. Define si su elección favorece, reduce o no cambia la compatibilidad.</p></header>{options.map((option, position) => <div key={position} className="screening-option"><label>Opción {position + 1}<AutoResizeTextarea value={option} maxLength={120} aria-label={`Opción ${position + 1}`} placeholder="Escribe la respuesta que podrá elegir el candidato" onChange={(event) => rename(position, event.target.value)} /></label><label>Valoración<select className="field-control" aria-label={`Efecto de la opción ${position + 1}`} value={Number(question.option_scores?.[option] || 0)} onChange={(event) => setScore(option, event.target.value)}><option value="5">+5 · Favorece mucho</option><option value="3">+3 · Favorece</option><option value="1">+1 · Favorece un poco</option><option value="0">0 · No cambia</option><option value="-1">−1 · Reduce un poco</option><option value="-3">−3 · Reduce</option><option value="-5">−5 · Reduce mucho</option></select></label><button type="button" className="button-ghost button-sm" onClick={() => removeOption(position)} aria-label={`Eliminar opción ${position + 1}`}><Trash2 size={15} /></button></div>)}{!options.length && <p className="screening-hint">Añade al menos dos opciones.</p>}<AddItemButton help={`${options.length}/12 opciones de respuesta`} disabled={options.length >= 12} onClick={() => onChange({ options: [...options, ""], option_scores: { ...(question.option_scores || {}) } })}>Añadir opción</AddItemButton></div>;
}
