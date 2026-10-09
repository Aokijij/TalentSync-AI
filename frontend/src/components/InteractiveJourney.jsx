import { useState } from "react";
import { ArrowLeft, ArrowRight, BadgeCheck, FlaskConical, Save } from "lucide-react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { ActivityInput, activityComplete, describeAnswer } from "./ActivityInput.jsx";

export function InteractiveJourney({ plan, onSaved, onClose }) {
  const { confirm } = useFeedback();
  const lab = plan.resource.journey, activities = lab.activities;
  const [values, setValues] = useState(plan.progress?.activity_answers || {}), [step, setStep] = useState(0);
  const [feedback, setFeedback] = useState(plan.progress?.activity_feedback || []), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const current = activities[step], complete = activities.filter((item) => activityComplete(item, values[item.id])).length;
  async function save(finish = false) {
    if (finish && !await confirm({ title: "Publicar tu muestra de trabajo", description: "El laboratorio se añadirá como práctica realizada a las evidencias de tu perfil. No equivale a una certificación profesional.", confirmLabel: "Publicar evidencia" })) return;
    setBusy(true); setError("");
    try { const { data } = await api.patch(`/learning/plans/${plan.resource.id}/journey`, { version: plan.version, activity_answers: values, finish }); setFeedback(data.find((row) => row.id === plan.id).progress.activity_feedback); await onSaved(data, finish); if (finish) setStep(3); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  const result = feedback.find((row) => row.question_id === current?.id);
  return <section className="journey-workspace space-y-6"><div className="flex flex-wrap justify-between gap-3"><button className="button-secondary" disabled={busy} onClick={async () => { if (JSON.stringify(values) === JSON.stringify(plan.progress?.activity_answers || {}) || await confirm({ title: "Volver al plan", description: "Tienes respuestas sin guardar. Puedes cancelar y guardar el borrador antes de salir.", confirmLabel: "Salir sin guardar" })) onClose(); }}><ArrowLeft size={16} />Volver al plan</button><span className="learning-tag">{plan.progress?.published ? "Evidencia publicada" : "Laboratorio interactivo"}</span></div>
    <header className="flex gap-4"><span className="learning-area-icon"><FlaskConical size={28} /></span><div><p className="section-kicker">Aprende haciendo</p><h2 className="text-2xl font-bold">{lab.lab_title}</h2><p className="mt-1 text-sm text-[var(--muted)]">Laboratorio inicial de 10–15 minutos. Ordena, calcula y conecta conceptos; practica y corrige cada actividad.</p></div></header>
    <div className="journey-case"><h3 className="font-bold">Tu misión</h3><p>{lab.lab_scenario}</p>{plan.resource.url && <><p className="text-sm text-[var(--muted)]">Este laboratorio complementa el curso. Finalizarlo no acredita haber completado la formación externa.</p><a className="text-[var(--accent)] underline" href={plan.resource.url} target="_blank" rel="noopener noreferrer">Consultar el curso externo</a></>}</div>
    <nav className="flex flex-wrap gap-2" aria-label="Actividades del laboratorio">{["Organiza el trabajo", "Resuelve el cálculo", "Conecta conceptos", "Tu resultado"].map((label, index) => <button className={step === index ? "button-primary" : "button-secondary"} key={label} onClick={() => setStep(index)} disabled={busy}>{index + 1}. {label}</button>)}</nav><progress className="w-full" max={3} value={complete} aria-label="Actividades respondidas" />
    {current ? <div className="space-y-5"><h3 className="text-xl font-bold">{current.prompt}</h3><ActivityInput item={current} value={values[current.id]} disabled={busy} onChange={(value) => { setValues({ ...values, [current.id]: value }); setFeedback(feedback.filter((row) => row.question_id !== current.id)); }} />
      {result && <div className={`activity-feedback ${result.correct ? "correct" : ""}`} role="status"><strong>{result.correct ? "Bien resuelto" : "Revisa tu decisión"}</strong><p className="mt-2 text-sm">{result.message}</p><p className="mt-2 text-xs">{result.correct ? "Continúa con la siguiente actividad." : "Aplica esta explicación, cambia tu respuesta y comprueba de nuevo."}</p></div>}
      <div className="flex flex-wrap gap-3"><button className="button-primary" disabled={busy || !activityComplete(current, values[current.id])} onClick={() => save()}>Comprobar mi respuesta</button><button className="button-secondary" disabled={busy || !result?.correct} onClick={() => setStep(step + 1)}>Continuar<ArrowRight size={16} /></button></div></div>
      : <div className="space-y-4"><h3 className="text-xl font-bold">Tu hoja de resultados</h3>{activities.map((item) => <article className="rounded-xl border border-[var(--line)] p-4" key={item.id}><h4 className="font-semibold">{item.prompt}</h4><p className="mt-2 text-sm">{describeAnswer(item, values[item.id])}</p><p className="mt-2 text-sm text-[var(--muted)]">{feedback.find((row) => row.question_id === item.id)?.correct ? "✓ Comprobado" : "Pendiente de revisar"}</p></article>)}<button className="button-primary" disabled={busy || feedback.length !== 3 || !feedback.every((row) => row.correct)} onClick={() => save(true)}><BadgeCheck size={18} />{plan.progress?.published ? "Actualizar mi evidencia" : "Finalizar y publicar evidencia"}</button><p className="text-xs text-[var(--muted)]">Práctica asistida con correcciones. Los retos evaluados por separado acreditan fundamentos.</p></div>}
    {error && <p role="alert" className="text-[var(--error)]">{error}</p>}<button disabled={busy} className="button-secondary" onClick={() => save()}><Save size={16} />Guardar borrador</button>
    {plan.progress?.published && <Link className="learning-published" to="/perfil#evidencias">Tu práctica ya está en el perfil. Ver evidencia →</Link>}
  </section>;
}
