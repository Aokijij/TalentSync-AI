import { useEffect, useState } from "react";
import { Save, X } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

export function ApplicationAnswersModal({ application, candidateName, onClose, onSaved }) {
  const [adjustments, setAdjustments] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setAdjustments(Object.fromEntries((application?.screening_answers || []).filter((item) => item.type !== "choice").map((item) => [item.question_id, Number(item.reviewer_adjustment || 0)])));
  }, [application]);
  if (!application) return null;
  const answers = application.screening_answers || [];
  const openAnswers = answers.filter((item) => item.type !== "choice");
  const base = Number(application.base_match_percentage ?? application.match_percentage ?? 0);
  const configuredAdjustment = answers.reduce((sum, item) => sum + Number(item.configured_adjustment || 0), 0);
  const manualAdjustment = Object.values(adjustments).reduce((sum, value) => sum + Number(value || 0), 0);
  const adjustment = configuredAdjustment + manualAdjustment;
  const final = Math.max(0, Math.min(100, base + adjustment));
  async function save() {
    setSaving(true); setError("");
    try {
      const { data } = await api.put(`/applications/${application.application_id || application.id}/status`, { screening_answer_adjustments: adjustments });
      await onSaved?.(data); onClose();
    } catch (requestError) { setError(getApiErrorMessage(requestError, "No fue posible guardar la valoración")); }
    finally { setSaving(false); }
  }
  return <div className="fixed inset-0 z-[90] grid place-items-center bg-slate-950/70 p-4 backdrop-blur-sm">
    <section role="dialog" aria-modal="true" className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl">
      <header className="flex items-start justify-between gap-4"><div><p className="section-kicker">Respuestas de postulación</p><h2 className="mt-1 text-2xl font-bold">{candidateName || application.candidate_name || "Candidato"}</h2><p className="mt-2 text-sm text-[var(--muted)]">Las opciones usan el efecto definido al crear la vacante. Tu equipo solo valora manualmente las respuestas abiertas.</p></div><button type="button" className="button-ghost !px-2" onClick={onClose} aria-label="Cerrar"><X size={20}/></button></header>
      <div className="mt-5 grid grid-cols-3 gap-3 text-center"><Metric label="Base del perfil" value={`${Math.round(base)}%`}/><Metric label="Ajuste total" value={`${adjustment > 0 ? "+" : ""}${adjustment}`}/><Metric label="Compatibilidad final" value={`${Math.round(final)}%`} accent/></div>
      {error ? <p className="mt-4 rounded-xl bg-[var(--error)]/10 p-3 text-sm text-[var(--error)]">{error}</p> : null}
      <div className="mt-5 space-y-3">{answers.map((item, index) => <article key={`${item.question_id}-${index}`} className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4"><p className="text-xs font-bold text-[var(--muted)]">{item.question || `Pregunta ${index + 1}`}</p><p className="mt-2 text-sm leading-6">{item.answer}</p>{item.type === "choice" ? <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-[var(--line)] pt-3 text-xs font-bold text-[var(--muted)]"><span>Efecto configurado al publicar</span><span className="rounded-lg border border-[var(--line)] bg-[var(--surface)] px-3 py-2 text-[var(--ink-strong)]">{Number(item.configured_adjustment || 0) > 0 ? "+" : ""}{Number(item.configured_adjustment || 0)} · Automático</span></div> : <label className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-[var(--line)] pt-3 text-xs font-bold text-[var(--muted)]"><span>Valoración manual de la empresa</span><select className="field-control input-sm w-48" value={adjustments[item.question_id] ?? 0} onChange={(event) => setAdjustments((current) => ({ ...current, [item.question_id]: Number(event.target.value) }))}>{[-3,-2,-1,0,1,2,3].map((value) => <option key={value} value={value}>{value > 0 ? `+${value}` : value} · {value === 0 ? "No cambia" : value > 0 ? "Suma" : "Resta"}</option>)}</select></label>}</article>)}{!answers.length ? <p className="rounded-xl border border-dashed border-[var(--line)] p-6 text-center text-sm text-[var(--muted)]">Esta vacante no tenía preguntas de postulación.</p> : null}</div>
      <footer className="mt-6 flex justify-end gap-3 border-t border-[var(--line)] pt-5"><button type="button" className="button-secondary" onClick={onClose}>{openAnswers.length ? "Cancelar" : "Cerrar"}</button>{openAnswers.length ? <button type="button" className="button-primary" disabled={saving} onClick={save}><Save size={16}/>{saving ? "Guardando…" : "Guardar valoración"}</button> : null}</footer>
    </section>
  </div>;
}

function Metric({ label, value, accent = false }) { return <div className={`rounded-xl border p-3 ${accent ? "border-[var(--accent)]" : "border-[var(--line)]"}`}><p className="text-xs text-[var(--muted)]">{label}</p><strong className={`mt-1 block text-xl ${accent ? "text-[var(--accent)]" : ""}`}>{value}</strong></div>; }
