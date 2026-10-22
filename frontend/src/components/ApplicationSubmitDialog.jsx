import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, FileText, Paperclip, Send } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { CoachDialog } from "./CoachDialog.jsx";
import { ResumePreferencesSummary } from "./ResumePreferencesSummary.jsx";
import { timestamp } from "../utils/dashboardData.js";
import "../styles/application-submit.css";

export function ApplicationSubmitDialog({ job, selectedVersion, onClose, onSubmitted }) {
  const [offer, setOffer] = useState(job), [pack, setPack] = useState(null);
  const [step, setStep] = useState("resume"), [answers, setAnswers] = useState({});
  const [choice, setChoice] = useState(selectedVersion ? "version" : "profile");
  const [versionId, setVersionId] = useState(selectedVersion?.id || "");
  const [loading, setLoading] = useState(true), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const [retry, setRetry] = useState(0), [preview, setPreview] = useState(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    Promise.all([api.get(`/jobs/${job.id}`, { signal: controller.signal }), api.get(`/profiles/me/coach/jobs/${job.id}/preparation`, { signal: controller.signal })]).then(([a, b]) => {
      if (controller.signal.aborted) return;
      setOffer(a.data); setPack(b.data); setStep(a.data.application_questions?.length ? "questions" : "resume");
      setVersionId((current) => current || b.data.versions[0]?.id || "");
    }).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure, "No pudimos preparar tu postulación.")); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [job.id, retry]);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  const questions = offer.application_questions || [];
  function validateAnswers() {
    const missing = questions.find((row) => row.required !== false && !String(answers[row.id] || "").trim());
    if (missing) { setError(`Responde la pregunta: ${missing.prompt}`); return false; }
    setError(""); return true;
  }
  async function submit() {
    if (busy || loading || !pack || !validateAnswers()) return;
    if (choice === "version" && !versionId) { setError("Selecciona una versión guardada."); return; }
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/applications", { job_id: job.id, attach_resume: choice !== "none", resume_version_id: choice === "version" ? versionId : null,
        screening_answers: Object.entries(answers).filter(([, value]) => String(value).trim()).map(([question_id, answer]) => ({ question_id, answer: String(answer).trim() })) }, { __quiet: true });
      onSubmitted(data);
    } catch (failure) { setError(getApiErrorMessage(failure, "No pudimos enviar tu postulación. Puedes intentarlo de nuevo.")); }
    finally { setBusy(false); }
  }
  async function previewPdf() {
    setBusy(true); setError("");
    try {
      const response = choice === "version" ? await api.get(`/profiles/me/coach/cv-versions/${versionId}/pdf`, { responseType: "blob" }) : await api.post("/profiles/me/export", pack.profile.resume_options, { responseType: "blob", __quiet: true });
      setPreview(URL.createObjectURL(response.data));
    } catch { setError("No pudimos abrir el PDF. Intenta revisarlo otra vez antes de enviar."); }
    finally { setBusy(false); }
  }
  return <CoachDialog open onClose={onClose} closeDisabled={busy} title="Revisa tu postulación" Icon={FileText} className="application-submit-dialog">
    <div className="application-submit-body"><div className="application-submit-context"><span>{offer.company_name}</span><h3>{offer.title}</h3></div>
      {!loading && !!questions.length && <p className="application-submit-step">{step === "questions" ? "1. Respuestas para la empresa" : "2. Hoja de vida y envío"}</p>}
      {loading && <p role="status">Preparando tu perfil y tus documentos…</p>}
      {!loading && pack && (step === "questions" ? <div className="application-submit-questions"><p>Responde con ejemplos reales. Los campos con * son obligatorios.</p>{questions.map((row, index) => <label key={row.id}>{index + 1}. {row.prompt}{row.required !== false && " *"}{row.type === "choice" ? <select className="field-control" value={answers[row.id] || ""} onChange={(event) => setAnswers({ ...answers, [row.id]: event.target.value })}><option value="">Selecciona una respuesta</option>{row.options.map((option) => <option key={option}>{option}</option>)}</select> : <textarea className="field-control" maxLength={2000} rows={3} value={answers[row.id] || ""} onChange={(event) => setAnswers({ ...answers, [row.id]: event.target.value })} />}</label>)}</div> : <>
        <div className="application-submit-heading"><Paperclip size={19} /><div><h3>¿Qué hoja de vida quieres adjuntar?</h3><p>Elige el documento que recibirá la empresa.</p></div></div>
        <fieldset className="application-resume-options" disabled={busy}><legend className="sr-only">Hoja de vida para esta postulación</legend>{[["profile", "Mi CV del perfil", "Con el diseño y los apartados que guardaste en tu perfil."], ...(pack.versions.length ? [["version", "Una versión guardada", "Selecciona un PDF que ya preparaste para esta vacante."]] : []), ["none", "Continuar sin adjunto", "La empresa podrá consultar tu perfil profesional, sin un PDF adjunto."]].map(([value, title, description]) => <label key={value} className={choice === value ? "is-selected" : ""}><input type="radio" name="application-resume" value={value} checked={choice === value} onChange={() => { setChoice(value); setPreview(null); }} /><span><strong>{title}</strong><small>{description}</small></span></label>)}</fieldset>
        {choice === "profile" && <ResumePreferencesSummary options={pack.profile.resume_options} compact />}
        {choice === "version" && <label className="application-version-picker">PDF guardado<select className="field-control" disabled={busy} value={versionId} onChange={(event) => { setVersionId(event.target.value); setPreview(null); }}>{pack.versions.map((row) => <option key={row.id} value={row.id}>{new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(new Date(timestamp(row.created_at)))} · {row.filename}</option>)}</select><small>Esta versión conserva el contenido con el que la guardaste.</small></label>}
        {choice !== "none" && <button type="button" className="button-secondary button-sm" disabled={busy} onClick={previewPdf}><FileText size={16} />Revisar PDF</button>}
        {preview && <iframe className="application-resume-preview" title="Vista previa de la hoja de vida a enviar" src={preview} />}
        <p className="application-submit-disclosure">Al enviar, compartes tu perfil y tus respuestas con {offer.company_name}. {choice !== "none" && "Se conservará una copia del PDF que adjuntes."}</p>
      </>)}
      {error && <p role="alert" className="application-submit-error">{error}{!pack && <button type="button" className="button-secondary button-sm" onClick={() => setRetry((current) => current + 1)}>Reintentar</button>}</p>}
    </div>
    <footer className="application-submit-footer"><button type="button" className="button-secondary" disabled={busy} onClick={step === "resume" && questions.length ? () => { setStep("questions"); setError(""); } : onClose}>{step === "resume" && questions.length ? <><ArrowLeft size={16} />Respuestas</> : "Cancelar"}</button><button type="button" className="button-primary" disabled={loading || busy || !pack} onClick={step === "questions" ? () => { if (validateAnswers()) setStep("resume"); } : submit}>{step === "questions" ? <>Elegir CV<ArrowRight size={16} /></> : <><Send size={16} />{busy ? "Procesando…" : "Enviar postulación"}</>}</button></footer>
  </CoachDialog>;
}
