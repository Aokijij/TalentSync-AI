import { responseState } from "../utils/responseDeadlines.js";
import { isProcessClosed } from "../utils/recruitmentState.js";
import { RecruiterProcessDialog } from "../components/RecruiterProcessDialog.jsx";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { InlineNotice } from "../components/ui/Panel.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { ApplicationPreparation } from "../components/ApplicationPreparation.jsx";
import { InterviewEvaluationPanel } from "../components/InterviewEvaluationPanel.jsx";
import { ProcessWorkspace, processLabels } from "../components/ProcessWorkspace.jsx";
import { Panel } from "../components/ui/Panel.jsx";

export function ProcessPage() {
  const { applicationId } = useParams();
  return <ProcessController key={applicationId} applicationId={applicationId} />;
}

function ProcessController({ applicationId }) {
  const { confirm } = useFeedback();
  const { user } = useAuth();
  const [process, setProcess] = useState(null), [error, setError] = useState("");
  const [manageInterview, setManageInterview] = useState(false);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    api.get(`/workflow/applications/${applicationId}`, { signal: controller.signal })
      .then(({ data }) => { if (!controller.signal.aborted) setProcess(data); })
      .catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure)); });
    return () => controller.abort();
  }, [applicationId]);

  async function saveProcess(changes, notice) {
    const { data } = await api.put(`/applications/${applicationId}/status`, { ...changes, expected_version: process.version }, { __quiet: true });
    setManageInterview(false);
    setProcess((current) => ({ ...current, ...data }));
    setMessage(notice); setError("");
    try { setProcess((await api.get(`/workflow/applications/${applicationId}`, { __quiet: true })).data); }
    catch { setError("El cambio quedó guardado. Actualiza la página para consultar el historial más reciente."); }
  }

  async function communicate(values) {
    if (busy) return false;
    if (!await confirm({ title: "Comunicar este avance", description: "El estado y el mensaje se guardarán en el historial y estarán disponibles para el candidato.", confirmLabel: "Guardar y comunicar" })) return false;
    setBusy(true); setError(""); setMessage("");
    try {
      const payload = { status: values.status, expected_version: process.version };
      if (values.message.trim()) payload.candidate_feedback = { message: values.message.trim(), reason_code: values.reason_code };
      await api.put(`/applications/${applicationId}/status`, payload, { __quiet: true });
      setProcess((await api.get(`/workflow/applications/${applicationId}`)).data);
      setMessage("Avance comunicado y guardado en el historial.");
      return true;
    } catch (failure) { setError(getApiErrorMessage(failure)); return false; }
    finally { setBusy(false); }
  }

  return <div className="process-page space-y-5">
    <PageHeader kicker="Seguimiento transparente" title={process?.job_title || "Tu proceso de selección"} description={user.role === "company" ? "Consulta el avance, prepara la entrevista y comunica el siguiente paso." : "Consulta el estado y los próximos pasos de tu postulación."} />
    {error && <InlineNotice error title="No pudimos actualizar el proceso">{error}</InlineNotice>}
    {message && <InlineNotice tone="success" title="Proceso actualizado">{message}</InlineNotice>}
    {!process && !error && <p role="status" className="text-sm text-[var(--muted)]">Cargando el proceso…</p>}
    {process && <>
      <ProcessWorkspace process={process} role={user.role} onProcessUpdated={(updated) => { setProcess(updated); setMessage("Nuevo compromiso guardado y comunicado al candidato."); }} onCompleteInterview={process.can_manage && !isProcessClosed(process) ? async () => { if (busy || !await confirm({ title: "Registrar entrevista realizada", description: "Se avisará al candidato que su entrevista se realizó y que está pendiente de respuesta. El plazo para comunicar la decisión comienza ahora.", confirmLabel: "Registrar y notificar" })) return; setBusy(true); try { await saveProcess({ interview_action: "complete" }, "Entrevista realizada. Registra la evaluación y comunica la decisión."); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } } : undefined} onManageInterview={process.can_manage && !isProcessClosed(process) ? () => setManageInterview(true) : undefined}
        evaluation={user.role === "company" ? <InterviewEvaluationPanel process={process} onSaved={setProcess} /> : null}
        communication={process.can_manage && !isProcessClosed(process) ? <CommunicationForm process={process} busy={busy} onCommunicate={communicate} /> : null}
        preparation={user.role === "candidate" ? <ApplicationPreparation applicationId={applicationId} jobId={process.job_id} /> : null}
      />
      {manageInterview && !isProcessClosed(process) && <RecruiterProcessDialog application={{ ...process, id: process.application_id }} onClose={() => setManageInterview(false)} onDelete={() => saveProcess({ status: "rejected", candidate_feedback: { reason_code: "other", message: "La empresa finalizó tu participación en este proceso de selección." } }, "Proceso finalizado y comunicado al candidato.")} onSave={(changes) => saveProcess(changes, "Entrevista actualizada. El cambio quedó en el historial y se notificó al candidato.")} />}
      <Link className="button-secondary inline-flex" to={user.role === "candidate" ? "/postulaciones" : user.role === "company" ? process.can_manage ? `/empresa/postulaciones?job=${process.job_id}` : "/empresa/equipo" : "/admin"}>Volver a mi espacio</Link>
    </>}
  </div>;
}

function CommunicationForm({ process, busy, onCommunicate }) {
  const [values, setValues] = useState({ status: process.status, message: "", reason_code: "other" });
  const change = (event) => setValues((current) => ({ ...current, [event.target.name]: event.target.value }));
  return <Panel title="Comunicar avance o resultado" description="El candidato podrá consultar este estado y el mensaje en su seguimiento." className="process-communicate">
    {responseState(process) === "paused" && <p className="text-sm text-[var(--muted)]">Para retomar el seguimiento, comunica un cambio de etapa o registra un nuevo compromiso desde el resumen. Enviar un mensaje conserva la etapa y el plazo actuales.</p>}
    <form onSubmit={async (event) => { event.preventDefault(); if (await onCommunicate(values)) setValues((current) => ({ ...current, message: "" })); }}>
      <label>Estado<select className="field-control" name="status" value={values.status} onChange={change} disabled={busy}>{Object.entries(processLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Motivo del feedback<select className="field-control" name="reason_code" value={values.reason_code} onChange={change} disabled={busy}><option value="other">Otro motivo</option><option value="skills_gap">Habilidades por acreditar</option><option value="experience_gap">Experiencia solicitada</option><option value="position_closed">Vacante cerrada</option></select></label>
      <label>Mensaje para el candidato (opcional)<textarea className="field-control" name="message" rows={4} minLength={10} maxLength={1500} placeholder="Describe evidencia concreta y cómo puede mejorar" value={values.message} onChange={change} disabled={busy} /></label>
      <footer><p>Los cambios se publican al guardar.</p><button disabled={busy} className="button-primary">{busy ? "Guardando…" : "Guardar y comunicar"}</button></footer>
    </form>
  </Panel>;
}
