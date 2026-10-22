import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, FileText, MessageSquare, RefreshCw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { CoachDialog } from "./CoachDialog.jsx";
import { PreparationWorkspace } from "./PreparationWorkspace.jsx";
import { InlineNotice } from "./ui/Panel.jsx";
import { preparationText, saveBlob } from "../utils/preparation.js";

export function ApplicationPreparation({ jobId, applicationId, selectedVersion, onVersionSelected }) {
  const { confirm } = useFeedback();
  const [open, setOpen] = useState(false), [tab, setTab] = useState(applicationId ? "interview" : "cv");
  const [data, setData] = useState(null), [form, setForm] = useState(null), [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  const [dirty, setDirty] = useState(false), [questionIndex, setQuestionIndex] = useState(0), [retry, setRetry] = useState(0), [preview, setPreview] = useState(null);
  const pendingVersion = useRef(null);
  const base = applicationId ? `/profiles/me/coach/applications/${applicationId}` : `/profiles/me/coach/jobs/${jobId}`;
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true); setError(""); setMessage("");
    api.get(`${base}/preparation`, { signal: controller.signal }).then(({ data: response }) => {
      if (controller.signal.aborted) return;
      setData(response); setAnswers(response.interview.answers); setDirty(false); setQuestionIndex(0);
      setForm({ summary: response.profile.summary, experiences: response.profile.experiences.map((_, index) => index), skills: response.profile.skills, style: "modern", includePhoto: true });
      pendingVersion.current = null;
    }).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure, "No pudimos cargar tu preparación.")); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [open, base, retry]);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview.url); }, [preview]);
  useEffect(() => {
    if (!dirty) return;
    const warn = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  async function close() {
    if (busy) return;
    if (dirty && !await confirm({ title: "Tienes respuestas sin guardar", description: "Puedes volver y guardarlas, o cerrar y descartar esta edición.", confirmLabel: "Cerrar sin guardar" })) return;
    setDirty(false); setOpen(false); setPreview(null);
  }
  async function perform(action) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (failure) {
      try { if (failure.response?.data instanceof Blob) failure.response.data = JSON.parse(await failure.response.data.text()); } catch { /* A non-JSON response uses the fallback below. */ }
      setError(getApiErrorMessage(failure, "No pudimos completar la acción. Tus textos siguen en esta ventana."));
    } finally { setBusy(false); }
  }
  async function createVersion() {
    await perform(async () => {
      pendingVersion.current ??= { request_key: crypto.randomUUID(), source_version: data.source_version, job_version: data.job_version, summary: form.summary, experience_indices: form.experiences, skills: form.skills, style: form.style, include_photo: form.includePhoto };
      const { data: version } = await api.post(`/profiles/me/coach/jobs/${jobId}/cv-versions`, pendingVersion.current, { __quiet: true });
      setData((current) => ({ ...current, versions: [version, ...current.versions.filter((row) => row.id !== version.id)] }));
      pendingVersion.current = null;
      setMessage("Versión guardada. Abre el PDF para revisarlo y elige «Usar al postularme» cuando esté listo.");
    });
  }
  async function pdf(row, download) {
    await perform(async () => {
      const url = applicationId ? `/applications/${applicationId}/resume` : `/profiles/me/coach/cv-versions/${row.id}/pdf`;
      const { data: blob } = await api.get(url, { responseType: "blob" });
      if (download) saveBlob(blob, row.filename);
      else setPreview({ url: URL.createObjectURL(blob), id: row.id });
    });
  }
  return <>
    <button type="button" className="preparation-launch" aria-haspopup="dialog" onClick={() => setOpen(true)}>{applicationId ? <MessageSquare size={21} /> : <FileText size={21} />}<span><strong>{applicationId ? "Prepara tu entrevista" : "Prepara tu postulación"}</strong><small>{applicationId ? "Practica y consulta el CV enviado" : "CV para esta vacante y práctica de entrevista"}</small></span><ArrowUpRight size={18} /></button>
    <CoachDialog open={open} onClose={close} closeDisabled={busy} title={applicationId ? "Tu preparación para el proceso" : "Prepara tu próxima oportunidad"} className="preparation-dialog" Icon={FileText}>
      {loading && <div className="preparation-loading" role="status"><RefreshCw size={19} className="animate-spin" />Cargando tu perfil y la oferta…</div>}
      {error && <div className="preparation-feedback"><InlineNotice error>{error}</InlineNotice><button className="button-secondary button-sm" type="button" disabled={busy} onClick={async () => { if (dirty && !await confirm({ title: "Recargar la preparación", description: "Descarga tus notas primero si quieres conservar esta edición. Recargar recuperará las respuestas guardadas.", confirmLabel: "Recargar" })) return; setRetry((value) => value + 1); }}>Recargar preparación</button></div>}
      {message && <div className="preparation-feedback"><InlineNotice>{message}</InlineNotice></div>}
      {data && form && !loading && <PreparationWorkspace data={data} tab={tab} onTab={setTab} form={form} onForm={(next) => { setForm(next); pendingVersion.current = null; }} busy={busy} saving={busy} answers={answers} onAnswer={(id, key, value) => { setAnswers((current) => ({ ...current, [id]: { ...current[id], [key]: value } })); setDirty(true); }} questionIndex={questionIndex} onQuestion={setQuestionIndex} dirty={dirty} onSaveInterview={() => perform(async () => {
        const { data: saved } = await api.put(`${base}/interview`, { expected_version: data.interview.version, revision: data.revision, answers }, { __quiet: true });
        setData((current) => ({ ...current, interview: { ...current.interview, ...saved, saved_at: saved.updated_at, outdated: false } })); setDirty(false); setMessage("Respuestas guardadas. Solo tú puedes consultarlas.");
      })} onDownloadNotes={() => saveBlob(new Blob([preparationText(data.job, data.interview.questions, answers)], { type: "text/plain;charset=utf-8" }), "Preparacion de entrevista - TalentSync.txt")} onCreateVersion={createVersion} onPreview={(row) => pdf(row, false)} onDownload={(row) => pdf(row, true)} onSelect={onVersionSelected ? (row) => onVersionSelected(selectedVersion?.id === row.id ? null : row) : undefined} selectedId={selectedVersion?.id} application={Boolean(applicationId)} preview={preview} onClosePreview={() => setPreview(null)} />}
    </CoachDialog>
  </>;
}
