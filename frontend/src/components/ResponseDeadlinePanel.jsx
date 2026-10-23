import { Link } from "react-router-dom";
import { useState } from "react";
import { CalendarPlus2, CheckCircle2, Clock3, PauseCircle } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { CoachDialog } from "./CoachDialog.jsx";
import { DateTimePicker } from "./DateTimePicker.jsx";
import { Panel } from "./ui/Panel.jsx";
import { interviewInputUtc, interviewInputValue } from "../utils/interviewAgenda.js";
import { proposedResponseDate, responseLabels, responseState, responseTime } from "../utils/responseDeadlines.js";
import "../styles/response-deadlines.css";

export function ResponseDeadlineBadge({ application }) {
  const state = responseState(application);
  if (!["overdue", "paused"].includes(state)) return null;
  const Icon = state === "paused" ? PauseCircle : Clock3;
  return <span className={`response-deadline-badge is-${state}`}><Icon size={14} />{responseLabels[state]}</span>;
}

export function ResponseDeadlinePanel({ process, role, onUpdated }) {
  const state = responseState(process), closed = state === "closed", company = role === "company";
  const remaining = Math.max(0, (process.deadline_policy?.extension_limit || 1) - (process.deadline_extension_count || 0));
  const [open, setOpen] = useState(false);
  const Icon = state === "paused" ? PauseCircle : state === "on_time" ? CheckCircle2 : Clock3;

  return <Panel title="Compromiso de respuesta" className={`response-deadline-panel is-${state}`} id="response-deadline">
    <div className="response-deadline-state"><Icon size={20} /><strong>{responseLabels[state]}</strong></div>
    {!closed && process.response_due_at && <div className="response-deadline-due"><small>{state === "on_time" ? "Responder antes de" : "Fecha comprometida"}</small><p className="response-deadline-date">{responseTime(process.response_due_at)}</p></div>}
    {state === "overdue" && <p className="response-deadline-explanation">La empresa superó la fecha comprometida. La candidatura se conserva; el equipo de selección debe comunicar un avance o una nueva fecha.</p>}
    {state === "paused" && <p className="response-deadline-explanation">El seguimiento está en pausa por falta de respuesta de la empresa. La etapa y la candidatura se conservan. Para retomar, la empresa debe comunicar un avance o registrar un nuevo compromiso.</p>}
    {state === "on_time" && <p className="response-deadline-explanation">Esta fecha corresponde al próximo mensaje de la empresa. La duración total de la selección se muestra por separado.</p>}
    {closed && <p className="response-deadline-explanation">El resultado y las comunicaciones se conservan en el historial.</p>}
    {!closed && <dl><div><dt>Responsable</dt><dd>{process.response_owner || `Equipo de selección de ${process.company_name}`}</dd></div><div><dt>Plazo de referencia por avance</dt><dd>{process.response_days} días laborables</dd></div>{process.pause_due_at && state === "overdue" && <div><dt>Pausa prevista si continúa sin respuesta</dt><dd>{responseTime(process.pause_due_at)}</dd></div>}</dl>}
    {role === "candidate" && state === "paused" && <div className="response-deadline-actions"><Link className="button-secondary" to={`/postulaciones?focus=${process.application_id}`}>Ver mis postulaciones</Link></div>}
    {company && process.can_manage && !closed && !open && <div className="response-deadline-actions">{remaining ? <button type="button" className="button-secondary" onClick={() => setOpen(true)}><CalendarPlus2 size={17} />{state === "paused" ? "Reanudar con nuevo plazo" : "Ampliar plazo"}</button> : <p>Ya se utilizó la ampliación de esta etapa. Comunica un avance o una decisión al candidato.</p>}</div>}
    {open && !closed && <DeadlineExtensionForm process={process} state={state} onClose={() => setOpen(false)} onSaved={(data) => { onUpdated?.(data); setOpen(false); }} />}
    {!closed && <p className="response-deadline-footnote">Los nuevos plazos cuentan de lunes a viernes, sin descontar festivos. Un retraso activa avisos y seguimiento; la selección conserva su etapa.</p>}
    <div className="response-deadline-created"><span>Postulación enviada</span><p>{responseTime(process.created_at)}</p>{process.process_estimated_end && <><span>Finalización estimada de la selección</span><p>{responseTime(process.process_estimated_end)}</p><small>Fecha orientativa. El cierre requiere un resultado comunicado.</small></>}</div>
  </Panel>;
}

function DeadlineExtensionForm({ process, state, onClose, onSaved }) {
  const { confirm } = useFeedback();
  const [date, setDate] = useState(() => interviewInputValue(proposedResponseDate(process.response_due_at))), [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  async function extend(event) {
    event.preventDefault();
    const due = interviewInputUtc(date);
    if (busy || !due) return;
    if (!await confirm({ title: state === "paused" ? "Reanudar con un nuevo compromiso" : "Ampliar el plazo de respuesta", description: `La empresa se compromete a responder antes del ${responseTime(due)}. El candidato recibirá el motivo y la nueva fecha. Esta ampliación se registra en el historial y se utiliza una vez por etapa.`, confirmLabel: "Confirmar y avisar" })) return;
    setBusy(true); setError("");
    try {
      const { data } = await api.post(`/workflow/applications/${process.application_id}/deadline-extension`, { expected_version: process.version, due_at: due, reason: reason.trim() }, { __quiet: true });
      onSaved(data);
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <CoachDialog open onClose={onClose} closeDisabled={busy} Icon={CalendarPlus2} title={state === "paused" ? "Nuevo compromiso de respuesta" : "Ampliar plazo de respuesta"} className="deadline-extension-dialog"><form className="response-extension-form" onSubmit={extend}><DateTimePicker label="Responder antes de · Colombia" value={date} onChange={setDate} /><label>Motivo que recibirá el candidato<textarea className="field-control" rows={3} required minLength={20} maxLength={500} value={reason} disabled={busy} onChange={(event) => setReason(event.target.value)} placeholder="Explica qué falta por revisar y cuándo comunicarás la decisión." /></label><small>Una ampliación por etapa, de hasta 7 días laborables adicionales. Si el plazo venció, cuentan desde hoy. Elige una fecha posterior al compromiso actual.</small>{error && <p role="alert" className="response-extension-error">{error}</p>}<div className="response-extension-actions"><button type="button" className="button-secondary" disabled={busy} onClick={onClose}>Cancelar</button><button type="submit" className="button-primary" disabled={busy || reason.trim().length < 20 || !interviewInputUtc(date)}><CalendarPlus2 size={16} />{busy ? "Guardando…" : "Revisar ampliación"}</button></div></form></CoachDialog>;
}
