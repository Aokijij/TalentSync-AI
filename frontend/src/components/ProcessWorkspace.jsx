import { isProcessClosed, recruitmentStage, interviewState, interviewStateLabels } from "../utils/recruitmentState.js";
import { CalendarClock, BriefcaseBusiness, ClipboardCheck, History, LayoutDashboard, MessageSquare, UserRound } from "lucide-react";
import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { responseState } from "../utils/responseDeadlines.js";
import { ResponseDeadlinePanel } from "./ResponseDeadlinePanel.jsx";
import { ProcessInterview } from "./InterviewAgenda.jsx";
import { StructuredJobText } from "./StructuredJobText.jsx";
import { Panel, WorkspaceTabs } from "./ui/Panel.jsx";
import { processDate } from "../utils/interviewAgenda.js";
import "../styles/process-workspace.css";

export const processLabels = { submitted: "Recibida", seen: "Vista", reviewing: "En revisión", shortlisted: "Preselección", technical_interview: "Entrevista técnica", psychometric_test: "Evaluación", accepted: "Seleccionado", hired: "Contratado", rejected: "Finalizado" };
export const processTime = (value, fallback = "Sin plazo activo") => processDate(value)?.toLocaleString("es-CO", { timeZone: "America/Bogota", dateStyle: "medium", timeStyle: "short" }) || fallback;

// Panels stay mounted: changing sections must not discard an evaluation or feedback draft.
export function ProcessWorkspace({ process, role, evaluation, communication, preparation, onManageInterview, onCompleteInterview, onProcessUpdated }) {
  const [tab, setTab] = useState("overview");
  const company = role === "company";
  const closed = isProcessClosed(process), interview = interviewState(process), response = responseState(process);
  const stage = recruitmentStage(process);
  const pipeline = process.job_conditions?.pipeline_stages || [];
  const activeIndex = pipeline.findIndex((item) => item.id === process.stage);
  const status = processLabels[process.status] || "En seguimiento";
  const items = [["overview", "Resumen", LayoutDashboard], ["vacancy", company ? "Preparar entrevista" : "La vacante", BriefcaseBusiness], ...(company ? [["evaluation", "Evaluación interna", ClipboardCheck]] : []), ["history", "Historial", History], ...(communication && !closed ? [["communicate", "Comunicar avance", MessageSquare]] : [])];
  const activeTab = items.some(([key]) => key === tab) ? tab : "overview";
  const panels = {
    overview: <div className="process-summary-grid">
      <div className="process-summary-main"><ProcessInterview process={process} />
        {process.feedback?.message ? <Panel title={process.feedback.source === "company" ? "Último mensaje de la empresa" : "Aviso del sistema"}><p className="process-feedback">{process.feedback.message}</p></Panel> : <Panel title="Próximo paso"><p>{closed ? "El proceso ha finalizado. Puedes consultar sus avances en el historial." : company ? response === "paused" ? "Retoma el proceso con un nuevo compromiso de respuesta o comunica una decisión al candidato." : interview === "scheduled" ? "La entrevista está programada. Revisa su fecha, acceso y preparación antes de realizarla." : interview === "unconfirmed" ? "La hora de la entrevista ya pasó. Confirma si se realizó o reprograma la cita." : interview === "awaiting_response" ? "La entrevista se realizó. Registra tu evaluación y comunica al candidato la decisión dentro del plazo indicado." : "Revisa las evidencias y registra tu evaluación antes de comunicar el siguiente avance." : "La empresa comunicará aquí los siguientes avances de tu postulación."}</p></Panel>}
        {(company || preparation || communication || onManageInterview && !closed || onCompleteInterview && interview === "unconfirmed") && <div className="process-quick-actions">{onManageInterview && !closed && <button type="button" className="button-secondary" onClick={onManageInterview}><CalendarClock size={17} />{interview === "awaiting_response" ? "Reprogramar entrevista" : process.interview_at ? "Gestionar entrevista" : "Programar entrevista"}</button>}{onCompleteInterview && interview === "unconfirmed" && <button type="button" className="button-primary" onClick={onCompleteInterview}><ClipboardCheck size={17} />Registrar entrevista realizada</button>}{company && <button type="button" className="button-secondary" onClick={() => setTab("evaluation")}><ClipboardCheck size={17} />{process.can_evaluate ? "Registrar evaluación" : "Consultar evaluaciones"}</button>}{communication && !closed && <button type="button" className="button-primary" onClick={() => setTab("communicate")}><MessageSquare size={17} />Comunicar avance</button>}{preparation}</div>}
      </div>
      <ResponseDeadlinePanel process={process} role={role} onUpdated={onProcessUpdated} />
    </div>,
    vacancy: <div className="process-vacancy-grid"><Panel title={company ? "Contexto y responsabilidades" : "Responsabilidades de la vacante"} description={company ? "Contrasta las tareas del cargo con ejemplos y evidencias de la entrevista." : undefined}><StructuredJobText text={process.job_description} /></Panel><div className="process-vacancy-side"><Panel title={company ? "Requisitos a contrastar" : "Requisitos de la vacante"}><StructuredJobText text={process.job_requirements} /></Panel>{process.job_id && <Link className="process-vacancy-link surface-card" to={`/vacantes/${process.job_id}`} state={{ returnTo: `/procesos/${process.application_id}` }}><BriefcaseBusiness size={21} /><span><strong>Ver vacante completa</strong><small>Consulta las condiciones y los requisitos de la oferta.</small></span><ArrowUpRight size={19} /></Link>}</div></div>,
    evaluation,
    history: <Panel title="Historial del proceso" description="Avances y comunicaciones, en orden cronológico."><ol className="process-timeline"><li><span aria-hidden="true" /><div><h3>Postulación creada</h3><p>{processTime(process.created_at)}</p></div></li>{(process.events || []).map((event) => <li key={event.id}><span aria-hidden="true" /><div><h3>{event.type === "application.response_overdue" ? "Respuesta atrasada de la empresa" : event.type === "application.response_paused" ? "En pausa por falta de respuesta de la empresa" : event.type === "application.deadline_extended" ? (event.resumed ? "Proceso retomado con nuevo compromiso" : "Plazo de respuesta ampliado") : event.type === "application.deadline_protected" ? "Plazo protegido por la entrevista" : event.type === "application.interview_completed" ? "Entrevista realizada · Pendiente de respuesta" : event.type === "application.interview_updated" ? ({ scheduled: "Entrevista programada", rescheduled: "Entrevista reprogramada", updated: "Detalles de entrevista actualizados", cancelled: "Entrevista cancelada" }[event.action] || "Entrevista actualizada") : event.type === "application.withdrawn" ? "Retirada por el candidato" : event.type === "application.deadline_released" ? "Plazo vencido; proceso cerrado" : event.type === "application.feedback_shared" ? "Feedback compartido" : `${processLabels[event.status] || event.status || "Avance del proceso"} · ${pipeline.find((item) => item.id === event.stage)?.title || processLabels[event.stage] || "En seguimiento"}`}</h3><p>{(event.extension_reason) && <>{event.extension_reason}<br /></>}{event.deadline && <>Compromiso de respuesta: {processTime(event.deadline)}<br /></>}{event.type === "application.interview_updated" && event.interview_at && <>{processTime(event.interview_at)} · {event.interview_mode === "virtual" ? "Virtual" : event.interview_mode === "in_person" ? "Presencial" : "Modalidad por confirmar"}<br /></>}{processTime(event.at)} · {event.source === "company" ? "Empresa" : event.source === "candidate" ? "Candidato" : "Sistema"}</p></div></li>)}</ol></Panel>,
    communicate: communication,
  };
  return <div className="process-workspace">
    <section className="process-identity surface-card" aria-label="Estado del proceso"><div><span className="process-status">{closed ? "Proceso cerrado" : response === "paused" ? "En pausa" : response === "overdue" ? "Respuesta atrasada" : status === stage ? "Proceso activo" : status}</span><h2>{stage}</h2>{interview && <p className="process-interview-state">{interviewStateLabels[interview]}</p>}<p>{process.company_name}{company && process.candidate_name && <> · <UserRound size={15} aria-hidden="true" />{process.candidate_name}</>}</p></div><button type="button" className="button-secondary button-sm" onClick={() => setTab("history")}><History size={16} />Ver historial</button></section>
    {!!pipeline.length && <ol className="process-stage-track" aria-label="Etapas de selección">{pipeline.map((item, index) => <li key={item.id} aria-current={item.id === process.stage ? "step" : undefined} className={index === activeIndex ? "is-current" : ""}><span>{index + 1}</span>{item.title}</li>)}</ol>}
    <WorkspaceTabs id="process" label="Secciones del seguimiento" value={activeTab} onChange={setTab} items={items} />
    {items.map(([key]) => <div key={key} role="tabpanel" id={`process-panel-${key}`} aria-labelledby={`process-tab-${key}`} tabIndex={0} hidden={activeTab !== key}>{panels[key]}</div>)}
  </div>;
}
