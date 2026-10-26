import { useCallback, useState } from "react";
import { ArrowLeft, BookOpen, CheckCircle2, Clock3, ExternalLink, Info, RotateCcw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { ExternalCertificateForm } from "./ExternalCertificateForm.jsx";
import { CourseChallenges } from "./CourseChallenges.jsx";
import { CourseSkillClaim } from "./CourseSkillClaim.jsx";
import { ResourceDetailsDialog } from "./ResourceDetailsDialog.jsx";
import { formatLearningHours } from "../utils/learningPresentation.js";
import { skillName } from "../utils/skillNames.js";
import "../styles/learning-paths.css";
import "../styles/course-flow.css";

export function CoursePlanWorkspace({ plan, onSaved, onClose, onReload }) {
  const { confirm } = useFeedback();
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [detailsOpen, setDetailsOpen] = useState(false);
  const completed = !!plan.progress?.course_completed, closeDetails = useCallback(() => setDetailsOpen(false), []);
  const noCertificate = plan.resource.details?.certificate_cost === "none" && !plan.certificate;
  async function update() {
    if (!await confirm({ title: completed ? "Retomar este curso" : "Marcar el curso como finalizado", description: completed ? "El curso volverá a tus recursos en marcha. Tus habilidades, retos y documentos aportados se conservan." : "Registrarás que terminaste la formación con el proveedor. Después podrás añadir tus habilidades y aportar el certificado si lo recibiste.", confirmLabel: completed ? "Retomar curso" : "Confirmar finalización" })) return;
    setBusy(true); setError("");
    try { const { data } = await api.patch(`/learning/plans/${plan.resource.id}/course`, { version: plan.version, completed: !completed }, { __successMessage: completed ? "Curso retomado en Mi plan." : "Finalización del curso registrada por ti." }); await onSaved(data, true); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  const detailButton = <button className="button-secondary course-flow-button" onClick={() => setDetailsOpen(true)}><Info size={17} />Detalle del curso</button>;
  return <section className={`course-workspace course-path course-flow ${completed ? "is-finished" : "is-running"}`} aria-label="Seguimiento del curso"><button className="button-ghost course-back-action" disabled={busy} onClick={onClose}><ArrowLeft size={16} />Volver al plan</button>
    <header className="course-path-heading"><span className="learning-area-icon">{completed ? <CheckCircle2 size={27} /> : <BookOpen size={27} />}</span><div><p className="section-kicker">{completed ? "MI PLAN · CURSO FINALIZADO" : "MI PLAN · FORMACIÓN"}</p><h2>{plan.resource.title}</h2><p>{plan.resource.provider} · {formatLearningHours(plan.resource.hours)} h estimadas</p></div><span className={`course-path-status ${completed ? "is-complete" : ""}`}>{completed ? <CheckCircle2 size={15} /> : <Clock3 size={15} />}{completed ? "Finalizado por ti" : "En marcha"}</span></header>
    {completed ? <>
      <section className="course-finish-banner"><CheckCircle2 size={30} /><div><h3>Has completado esta formación</h3><p>{noCertificate ? "Este curso no anuncia certificado. Registra las habilidades que aprendiste y sigue practicando a tu ritmo." : plan.certificate ? "Tu certificado está aportado. Revisa las habilidades que quieres incorporar a tu perfil." : "Ahora puedes incorporar lo aprendido y guardar el certificado del proveedor, si lo recibiste."}</p><small>La finalización la has registrado tú; no sustituye una evaluación del proveedor.</small></div></section>
      {!noCertificate && <ExternalCertificateForm plan={plan} onChanged={onReload} />}
      <CourseSkillClaim plan={plan} onSaved={onSaved} />
      <details className="finished-course-challenges"><summary>Seguir practicando las habilidades del curso</summary><CourseChallenges plan={plan} /></details>
      <footer className="course-finished-actions"><div>{detailButton}<a className="button-secondary course-flow-button" href={plan.resource.url} target="_blank" rel="noopener noreferrer">Consultar contenido<ExternalLink size={16} /></a></div><button className="button-ghost course-retake-action" disabled={busy} onClick={update}><RotateCcw size={16} />Retomar curso</button></footer>
    </> : <>
      <section className="course-study-panel"><div><p className="section-kicker">TU FORMACIÓN</p><h3>Continúa con el proveedor</h3><p>{plan.resource.instructions}</p><div className="course-path-skills">{plan.resource.skills.map((skill) => <span className="learning-skill" key={skill}>{skillName(skill)}</span>)}</div></div><div className="course-study-actions"><a className="button-primary course-flow-button" href={plan.resource.url} target="_blank" rel="noopener noreferrer">Continuar curso<ExternalLink size={17} /></a><button className="button-secondary course-flow-button" disabled={busy} onClick={update}><CheckCircle2 size={17} />Ya terminé el curso</button>{detailButton}<small>Estudia en {plan.resource.provider}. Al finalizar podrás registrar tus habilidades y, si corresponde, el certificado.</small></div></section>
      <CourseChallenges plan={plan} />
    </>}
    {error && <div className="welcome-alert" role="alert"><p>{error}</p><button className="button-secondary" disabled={busy} onClick={onReload}>Actualizar plan</button></div>}
    {detailsOpen && <ResourceDetailsDialog resource={plan.resource} inPlan onClose={closeDetails} />}
  </section>;
}
