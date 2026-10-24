import { useState } from "react";
import { ArrowLeft, BookOpen, CheckCircle2, Clock3, ExternalLink, FlaskConical, RotateCcw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { ExternalCertificateForm } from "./ExternalCertificateForm.jsx";
import { CourseChallenges } from "./CourseChallenges.jsx";
import { formatLearningHours } from "../utils/learningPresentation.js";
import "../styles/learning-paths.css";

export function CoursePlanWorkspace({ plan, onSaved, onClose, onPractice, onReload }) {
  const { confirm } = useFeedback();
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const completed = !!plan.progress?.course_completed, lab = plan.resource.journey;
  async function update() {
    if (!await confirm({ title: completed ? "Retomar este curso" : "Marcar el curso como finalizado", description: completed ? "El curso volverá a tus recursos en marcha. Tus retos y certificados se conservan." : "Registrarás que terminaste la formación con el proveedor. Los retos y el certificado se gestionan por separado.", confirmLabel: completed ? "Retomar curso" : "Confirmar finalización" })) return;
    setBusy(true); setError("");
    try { const { data } = await api.patch(`/learning/plans/${plan.resource.id}/course`, { version: plan.version, completed: !completed }, { __successMessage: completed ? "Curso retomado en Mi plan." : "Finalización del curso registrada por ti." }); await onSaved(data, true); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <section className="course-workspace course-path" aria-label="Seguimiento del curso"><button className="button-secondary button-sm" disabled={busy} onClick={onClose}><ArrowLeft size={16} />Volver al plan</button>
    <header className="course-path-heading"><span className="learning-area-icon"><BookOpen size={27} /></span><div><p className="section-kicker">MI PLAN · FORMACIÓN</p><h2>{plan.resource.title}</h2><p>{plan.resource.provider} · {formatLearningHours(plan.resource.hours)} h estimadas</p></div><span className={`course-path-status ${completed ? "is-complete" : ""}`}>{completed ? <CheckCircle2 size={15} /> : <Clock3 size={15} />}{completed ? "Finalizado por ti" : "En marcha"}</span></header>
    <section className="course-study-panel"><div><p className="section-kicker">TU FORMACIÓN</p><h3>{completed ? "Curso finalizado" : "Continúa con el proveedor"}</h3><p>{plan.resource.instructions}</p><div className="course-path-skills">{plan.resource.skills.map((skill) => <span className="learning-skill" key={skill}>{skill}</span>)}</div></div><div className="course-study-actions"><a className="button-primary" href={plan.resource.url} target="_blank" rel="noopener noreferrer">Abrir curso<ExternalLink size={17} /></a><button className={`button-secondary ${completed ? "is-complete" : ""}`} disabled={busy} onClick={update}>{completed ? <RotateCcw size={17} /> : <CheckCircle2 size={17} />}{completed ? "Retomar curso" : "Ya terminé el curso"}</button><small>La inscripción y el contenido se gestionan en {plan.resource.provider}. Aquí registras tu avance.</small></div></section>
    {error && <div className="welcome-alert" role="alert"><p>{error}</p><button className="button-secondary" disabled={busy} onClick={onReload}>Actualizar plan</button></div>}
    <CourseChallenges plan={plan} />
    {lab && <details className="course-previous-practice"><summary>Práctica complementaria de este plan</summary><p>{lab.lab_title || lab.title} · {lab.binding?.rationale || "Se conserva el ejercicio de tu plan anterior y sus respuestas."}</p><button className="button-secondary button-sm" disabled={busy} onClick={onPractice}><FlaskConical size={16} />{plan.progress?.submitted ? "Ver resultado de la práctica" : "Abrir práctica"}</button></details>}
    <ExternalCertificateForm plan={plan} onChanged={onReload} />
  </section>;
}
