import { useState } from "react";
import { ArrowLeft, ArrowRight, BookOpen, CheckCircle2, ExternalLink, FlaskConical, RotateCcw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { ExternalCertificateForm } from "./ExternalCertificateForm.jsx";
import { formatLearningHours } from "../utils/learningPresentation.js";
import "../styles/learning-revision.css";

export function CoursePlanWorkspace({ plan, onSaved, onClose, onPractice, onReload }) {
  const { confirm } = useFeedback();
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const completed = !!plan.progress?.course_completed, lab = plan.resource.journey;
  async function update() {
    if (!await confirm({ title: completed ? "Retomar este curso" : "Marcar el curso como finalizado", description: completed ? "El curso volverá a tus recursos en marcha. Tus prácticas y documentos se conservan." : "Registrarás que terminaste la formación con el proveedor. Esto no aprueba una práctica ni valida un certificado.", confirmLabel: completed ? "Retomar curso" : "Confirmar finalización" })) return;
    setBusy(true); setError("");
    try {
      const { data } = await api.patch(`/learning/plans/${plan.resource.id}/course`, { version: plan.version, completed: !completed }, { __successMessage: completed ? "Curso retomado en Mi plan." : "Finalización del curso registrada por ti." });
      await onSaved(data, true);
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="course-workspace space-y-5" aria-label="Seguimiento del curso"><button className="button-secondary button-sm" disabled={busy} onClick={onClose}><ArrowLeft size={16} />Volver al plan</button>
    <header className="course-workspace-heading"><span className="learning-area-icon"><BookOpen size={24} /></span><div><p className="section-kicker">FORMACIÓN CON EL PROVEEDOR</p><h2>{plan.resource.title}</h2><p>{plan.resource.provider} · {formatLearningHours(plan.resource.hours)} h estimadas</p></div><span className="learning-tag">{completed ? "Finalizado por ti" : "En marcha"}</span></header>
    <div className="course-tracking-grid"><section className="ui-panel"><div className="ui-panel-heading"><div><h3>1. Estudia el curso</h3><p>El contenido y la inscripción se gestionan en el sitio del proveedor. Añadirlo al plan no te inscribe.</p></div></div><div className="ui-panel-content"><p>{plan.resource.instructions}</p><div className="course-workspace-actions"><a className="button-primary" href={plan.resource.url} target="_blank" rel="noopener noreferrer">Abrir curso<ExternalLink size={16} /></a><button className="button-secondary" disabled={busy} onClick={update}>{completed ? <RotateCcw size={16} /> : <CheckCircle2 size={16} />}{completed ? "Retomar curso" : "Ya terminé el curso"}</button></div><small>El avance del curso es una declaración tuya y se guarda separado de los resultados de TalentSync.</small></div></section>
    <section className="ui-panel"><div className="ui-panel-heading"><div><h3>2. Practica si lo necesitas</h3><p>Una práctica mide solo las actividades indicadas; no sustituye la evaluación del proveedor.</p></div></div><div className="ui-panel-content">{lab ? <><span className="learning-tag">{lab.binding ? "Asociación revisada en el catálogo" : "Práctica de un plan anterior"}</span><h4 className="font-bold mt-3">{lab.lab_title || lab.title}</h4><p className="mt-2">{lab.binding?.rationale || "Se conserva para que consultes tu avance anterior. No se ha confirmado que cubra el temario de este curso."}</p><button className="button-secondary mt-4" disabled={busy} onClick={onPractice}><FlaskConical size={16} />{plan.progress?.submitted ? "Ver resultado de la práctica" : "Abrir práctica"}<ArrowRight size={15} /></button></> : <><p>No hay una práctica asociada a este curso. Puedes estudiarlo y aportar su certificado sin resolver un ejercicio diferente.</p><p className="mt-3 text-[var(--muted)]">Administración puede revisar una práctica del catálogo o redactar actividades que correspondan a su temario.</p></>}</div></section></div>
    {error && <div className="welcome-alert" role="alert"><p>{error}</p><button className="button-secondary" disabled={busy} onClick={onReload}>Actualizar plan</button></div>}
    <section><h3 className="text-lg font-bold mb-3">3. Aporta el certificado si lo recibiste</h3><ExternalCertificateForm plan={plan} onChanged={onReload} /></section>
  </section>;
}
