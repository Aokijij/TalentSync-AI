import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, MessageSquare, Save } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { CoachDialog } from "./CoachDialog.jsx";
import { answerAdjustment, applicationBaseMatch, projectedMatch } from "../utils/applicationMatch.js";
import "../styles/recruiter-dialog.css";

export function ApplicationAnswersModal({ application, candidateName, onClose, onSaved, onPrepare, loadCompatibility }) {
  if (!application) return null;
  return <AnswersEditor key={application.application_id || application.id} {...{ application, candidateName, onClose, onSaved, onPrepare, loadCompatibility }} />;
}

function AnswersEditor({ application, candidateName, onClose, onSaved, onPrepare, loadCompatibility }) {
  const answers = application.screening_answers || [];
  const [index, setIndex] = useState(0);
  const [adjustments, setAdjustments] = useState(() => application.screening_answer_adjustments || Object.fromEntries(answers.filter((item) => item.type !== "choice").map((item) => [item.question_id, Number(item.reviewer_adjustment || 0)])));
  const [saving, setSaving] = useState(false), [error, setError] = useState("");
  const current = answers[index];
  const knownBase = applicationBaseMatch(application);
  const [loadedBase, setLoadedBase] = useState(null), [matchError, setMatchError] = useState("");
  const [matchLoading, setMatchLoading] = useState(knownBase == null), [retry, setRetry] = useState(0);
  const loader = useRef(loadCompatibility);
  loader.current = loadCompatibility;
  const base = knownBase ?? loadedBase;
  const adjustment = answerAdjustment(answers, adjustments);
  const final = projectedMatch(base, adjustment);
  useEffect(() => {
    if (knownBase != null) return;
    const controller = new AbortController();
    setMatchLoading(true); setMatchError("");
    const request = loader.current ? loader.current() : application.job_id && application.user_id
      ? api.get(`/recommendations/jobs/${application.job_id}/candidates/${application.user_id}/explanation`, { signal: controller.signal, __quiet: true }).then(({ data }) => data)
      : Promise.reject(new Error("missing-match-context"));
    request.then((data) => {
      if (controller.signal.aborted) return;
      const value = applicationBaseMatch(data);
      if (value == null) throw new Error("missing-base-match");
      setLoadedBase(value);
    }).catch((failure) => {
      if (!controller.signal.aborted) setMatchError(getApiErrorMessage(failure, "No pudimos calcular la compatibilidad. Puedes seguir revisando las respuestas."));
    }).finally(() => { if (!controller.signal.aborted) setMatchLoading(false); });
    return () => controller.abort();
  }, [knownBase, application.job_id, application.user_id, retry]);
  async function save() {
    if (saving) return;
    setSaving(true); setError("");
    try {
      if (onPrepare) await onPrepare({ screening_answer_adjustments: adjustments });
      else {
        const { data } = await api.put(`/applications/${application.application_id || application.id}/status`, { screening_answer_adjustments: adjustments, expected_version: application.version }, { __quiet: true });
        await onSaved?.(data); onClose();
      }
    } catch (failure) { setError(getApiErrorMessage(failure, "No pudimos guardar la valoración. Tus cambios siguen aquí.")); }
    finally { setSaving(false); }
  }
  return <CoachDialog open title="Respuestas de postulación" Icon={MessageSquare} className="answers-dialog" onClose={onClose} closeDisabled={saving}>
    <div className="answers-workspace"><p className="answers-context"><strong>{candidateName || application.candidate_name || "Candidato"}</strong><br />Revisa cada respuesta. Las preguntas con opciones conservan la valoración definida al publicar.</p>
      <div className="answers-metrics" aria-live="polite" aria-busy={base == null && matchLoading}>{[["Base del perfil", base == null ? matchLoading ? "Calculando…" : "No disponible" : `${Math.round(base)}%`], ["Ajuste total", `${adjustment > 0 ? "+" : ""}${adjustment} pts`], ["Compatibilidad proyectada", final == null ? matchLoading ? "Calculando…" : "No disponible" : `${Math.round(final)}%`]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
      {base == null && matchError && <div className="ui-inline-notice is-error" role="alert"><p>{matchError}</p><button type="button" className="button-secondary button-sm mt-2" disabled={matchLoading} onClick={() => setRetry((value) => value + 1)}>Reintentar compatibilidad</button></div>}
      <p className="answers-context">Base del perfil actual + valoración de respuestas. La proyección es privada para la empresa.</p>
      {error && <p role="alert" className="ui-inline-notice is-error">{error}</p>}
      {current ? <section className="answers-question"><p>Pregunta {index + 1} de {answers.length}</p><h3>{current.question || `Pregunta ${index + 1}`}</h3><div className="answers-response">{current.answer}</div>{current.type === "choice" ? <p className="answers-rating">Efecto configurado al publicar: {Number(current.configured_adjustment || 0) > 0 ? "+" : ""}{Number(current.configured_adjustment || 0)} · Automático</p> : <label className="answers-rating">Valoración manual de la empresa<select className="field-control" disabled={saving} value={adjustments[current.question_id] ?? 0} onChange={(event) => setAdjustments((values) => ({ ...values, [current.question_id]: Number(event.target.value) }))}>{[-3, -2, -1, 0, 1, 2, 3].map((value) => <option key={value} value={value}>{value > 0 ? `+${value}` : value} · {value === 0 ? "No cambia" : value > 0 ? "Suma" : "Resta"}</option>)}</select></label>}
        {answers.length > 1 && <nav className="answers-question-nav" aria-label="Respuestas de postulación"><button type="button" className="button-secondary button-sm" disabled={index === 0 || saving} onClick={() => setIndex(index - 1)}><ChevronLeft size={16} />Anterior</button><span>{index + 1} / {answers.length}</span><button type="button" className="button-secondary button-sm" disabled={index === answers.length - 1 || saving} onClick={() => setIndex(index + 1)}>Siguiente<ChevronRight size={16} /></button></nav>}
      </section> : <p className="answers-empty">Esta vacante no tenía preguntas de postulación.</p>}
      {onPrepare && <p className="answers-context">La valoración se aplicará al guardar los cambios pendientes del tablero.</p>}
      <footer className="answers-footer"><button type="button" className="button-secondary" disabled={saving} onClick={onClose}>Cerrar</button>{answers.some((item) => item.type !== "choice") && <button type="button" className="button-primary" disabled={saving} onClick={save}><Save size={16} />{saving ? "Guardando…" : onPrepare ? "Preparar valoración" : "Guardar valoración"}</button>}</footer>
    </div>
  </CoachDialog>;
}
