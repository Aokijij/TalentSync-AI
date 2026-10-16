import { Plus, Trash2 } from "lucide-react";

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
  return (
    <section className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">Preguntas antes de postularse</h3>
          <p className="mt-1 max-w-2xl text-sm text-[var(--muted)]">En preguntas de selección defines ahora cuánto suma o resta cada opción. Las respuestas abiertas se valoran manualmente después de la postulación.</p>
        </div>
        <button type="button" className="button-outline button-sm" disabled={value.length >= 10} onClick={add}><Plus size={15} />Agregar pregunta</button>
      </div>
      <div className="mt-4 space-y-4">
        {value.map((question, index) => (
          <article key={question.id} className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4">
            <div className="flex items-start gap-3">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--accent)]/10 text-sm font-bold text-[var(--accent)]">{index + 1}</span>
              <div className="grid min-w-0 flex-1 gap-3 md:grid-cols-[1fr_170px]">
                <label className="text-sm font-semibold text-[var(--muted)]">Pregunta<input className="field-control mt-1" value={question.prompt} maxLength={300} placeholder="Ej. ¿Tienes disponibilidad para trabajar los sábados?" onChange={(event) => update(index, { prompt: event.target.value })} /></label>
                <label className="text-sm font-semibold text-[var(--muted)]">Tipo<select className="field-control mt-1" value={question.type} onChange={(event) => update(index, { type: event.target.value, options: [], option_scores: {} })}><option value="open">Respuesta abierta</option><option value="choice">Elegir una opción</option></select></label>
              </div>
              <button type="button" className="button-ghost button-sm !px-2 text-[var(--error)]" onClick={() => remove(index)} aria-label="Eliminar pregunta"><Trash2 size={16} /></button>
            </div>
            <div className="ml-11 mt-4 space-y-4">
              {question.type === "choice" ? (
                <ChoiceOptions question={question} onChange={(changes) => update(index, changes)} />
              ) : (
                <p className="rounded-lg border border-[var(--line)] bg-[var(--surface-subtle)] px-4 py-3 text-sm leading-6 text-[var(--muted)]">El candidato podrá explicar su respuesta con sus propias palabras. Tu equipo la verá completa y esta pregunta no modificará automáticamente la compatibilidad.</p>
              )}
              <label className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--ink-strong)]"><input type="checkbox" checked={question.required ?? true} onChange={(event) => update(index, { required: event.target.checked })} />Respuesta obligatoria</label>
            </div>
          </article>
        ))}
        {!value.length ? <p className="rounded-lg border border-dashed border-[var(--line)] px-4 py-6 text-center text-sm text-[var(--muted)]">No se pedirán respuestas adicionales.</p> : null}
      </div>
    </section>
  );
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
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div><p className="text-sm font-bold text-[var(--ink-strong)]">Opciones y efecto automático</p><p className="mt-1 text-xs leading-5 text-[var(--muted)]">El puntaje elegido se aplicará cuando el candidato seleccione esa opción.</p></div>
        <button type="button" className="button-secondary button-sm" disabled={options.length >= 12} onClick={() => onChange({ options: [...options, ""], option_scores: { ...(question.option_scores || {}) } })}><Plus size={14} />Añadir opción</button>
      </div>
      <div className="mt-3 space-y-2">
        {options.map((option, position) => (
          <div key={position} className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_220px_auto] sm:items-center">
            <input className="field-control" value={option} maxLength={120} aria-label={`Opción ${position + 1}`} placeholder={`Opción ${position + 1}`} onChange={(event) => rename(position, event.target.value)} />
            <select className="field-control" aria-label={`Efecto de la opción ${position + 1}`} value={Number(question.option_scores?.[option] || 0)} onChange={(event) => setScore(option, event.target.value)}><option value="5">+5 · Favorece mucho</option><option value="3">+3 · Favorece</option><option value="1">+1 · Favorece un poco</option><option value="0">0 · No cambia</option><option value="-1">−1 · Reduce un poco</option><option value="-3">−3 · Reduce</option><option value="-5">−5 · Reduce mucho</option></select>
            <button type="button" className="button-ghost button-sm !px-2 text-[var(--error)]" onClick={() => removeOption(position)} aria-label={`Eliminar opción ${position + 1}`}><Trash2 size={15} /></button>
          </div>
        ))}
        {!options.length ? <p className="rounded-lg border border-dashed border-[var(--line)] px-3 py-4 text-center text-sm text-[var(--muted)]">Añade al menos dos opciones, una por fila.</p> : null}
      </div>
    </div>
  );
}

