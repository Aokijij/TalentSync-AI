import { ArrowLeft, ArrowRight, CalendarClock, ClipboardList, ExternalLink, FileText, History, UserRound, X } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";
import { api, getApiErrorMessage } from "../../api/client.js";
import { saveBlob } from "../../utils/preparation.js";
import { isProcessClosed, recruitmentStage, interviewState, interviewStateLabels } from "../../utils/recruitmentState.js";
import { ResponseDeadlineBadge } from "../ResponseDeadlinePanel.jsx";
import { InterviewDetails } from "../InterviewDetails.jsx";

export function ApplicantScore({ row }) {
  const score = row.adjusted_match_percentage;
  return <span className={`applicant-score ${score == null ? "is-missing" : ""}`}><strong>{score == null ? "Sin cálculo" : `${Math.round(score)}%`}</strong>{score != null && <span role="progressbar" aria-label="Compatibilidad" aria-valuenow={Math.round(score)} aria-valuemin={0} aria-valuemax={100}><i style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></span>}</span>;
}

export function ApplicantDetail({ data, loading, error, busy, nextStage, onNextStage, stages, allStages, onCompleteInterview, onAdvance, onReject, onHire, onManage, onAnswers, onClose, onRetry }) {
  const [downloadError, setDownloadError] = useState(""), [downloading, setDownloading] = useState(false);
  if (!data) return <aside className="applicant-detail is-empty" aria-label="Detalle de candidatura"><UserRound size={32} /><h2>{loading ? "Abriendo candidatura…" : "Revisa una candidatura"}</h2><p role={error ? "alert" : loading ? "status" : undefined}>{error || "Selecciona una persona para consultar su perfil, respuestas y siguientes pasos."}</p>{error && <button className="button-secondary" onClick={onRetry}>Volver a intentar</button>}</aside>;
  const { application: row, profile } = data;
  const closed = isProcessClosed(row), interview = interviewState(row);
  async function download() {
    setDownloading(true); setDownloadError("");
    try { const { data: pdf } = await api.get(`/applications/${row.id}/resume`, { responseType: "blob", __quiet: true }); saveBlob(pdf, `Hoja de vida - ${row.candidate_name}.pdf`); }
    catch (failure) { setDownloadError(getApiErrorMessage(failure, "No pudimos descargar el CV. Inténtalo de nuevo.")); }
    finally { setDownloading(false); }
  }
  return <aside className="applicant-detail" aria-label="Detalle de candidatura" aria-busy={loading}>
    <header><button type="button" className="button-ghost applicant-back" onClick={onClose}><ArrowLeft size={16} />Volver a la lista</button><div><span className="section-kicker">{row.identity_hidden ? "Perfil anónimo" : "Candidatura"}</span><h2>{row.candidate_name}</h2><p>{profile?.profession || "Perfil profesional por completar"}</p><span className="recruitment-stage-badge">{recruitmentStage(row, allStages)}</span><ResponseDeadlineBadge application={row} />{interview && <small className="applicant-interview-state">{interviewStateLabels[interview]}</small>}</div><button type="button" className="button-ghost applicant-close" onClick={onClose} aria-label="Cerrar detalle"><X size={18} /></button></header>
    <div className="applicant-match"><div><ApplicantScore row={row} /><span>Compatibilidad {row.screening_adjustment ? "ajustada" : "del perfil"}</span></div><small>Orientación para revisar evidencias. No representa una probabilidad de contratación.</small></div>
    {error && <p role="alert" className="recruitment-error">{error}<button className="button-ghost button-sm" onClick={onRetry}>Actualizar perfil</button></p>}
    <div className="applicant-detail-tools"><Link to={`/procesos/${row.id}`} className="button-secondary button-sm"><History size={15} />Ver proceso</Link>{!closed && <Link to={`/procesos/${row.id}#response-deadline`} className="button-secondary button-sm">Gestionar plazo</Link>}{!closed && <button type="button" className="button-secondary button-sm" disabled={busy || loading} onClick={onManage}><CalendarClock size={15} />{interview === "awaiting_response" ? "Reprogramar entrevista" : row.interview_at ? "Gestionar entrevista" : "Programar entrevista"}</button>}{!!row.screening_answers?.length && <button type="button" className="button-secondary button-sm" onClick={onAnswers} disabled={busy || loading}><ClipboardList size={15} />{closed ? "Ver respuestas" : "Respuestas"} ({row.screening_answers.length})</button>}{profile?.submitted_resume_url && <button type="button" className="button-secondary button-sm" disabled={downloading} onClick={download}><FileText size={15} />{downloading ? "Descargando…" : "Descargar CV"}</button>}<Link to={`/empresa/candidatos/${row.user_id}?job=${row.job_id}`} className="applicant-full-profile">Perfil completo<ExternalLink size={13} /></Link></div>
    {downloadError && <p role="alert" className="recruitment-error">{downloadError}</p>}
    <div className="applicant-detail-content">
      {profile?.experience && <section><h3>Resumen profesional</h3><p>{profile.experience}</p></section>}
      {!!profile?.skills?.length && <section><h3>Habilidades del perfil</h3><div className="applicant-skills">{profile.skills.map((skill) => <span key={skill}>{skill}</span>)}</div></section>}
      {!!profile?.experiences?.length && <section><h3>Experiencia</h3>{profile.experiences.map((item, index) => <article key={index}><strong>{item.role || "Experiencia profesional"}</strong><small>{[item.company, item.start_date || item.start_year, item.is_current ? "Actualidad" : item.end_date || item.end_year].filter(Boolean).join(" · ")}</small>{item.description && <p>{item.description}</p>}</article>)}</section>}
      {!!profile?.educations?.length && <section><h3>Formación</h3>{profile.educations.map((item, index) => <article key={index}><strong>{item.degree || item.title || "Formación académica"}</strong><small>{[item.institution, item.is_current ? "En curso" : item.end_year].filter(Boolean).join(" · ")}</small></article>)}</section>}
      {interview === "unconfirmed" && <section className="interview-next-action"><h3>Confirma si se realizó la entrevista</h3><p>La fecha ya pasó. Registra que se realizó o reprograma si quedó pendiente.</p><button className="button-primary button-sm" disabled={busy || loading} onClick={onCompleteInterview}>Registrar entrevista realizada</button></section>}{interview === "awaiting_response" && <section className="interview-next-action"><h3>El candidato espera tu respuesta</h3><p>Consulta la evaluación desde Ver proceso y comunica la decisión para continuar o finalizar su participación.</p></section>}{row.interview_at && <section><h3>Entrevista</h3><InterviewDetails details={row.interview_details} /></section>}
      {!profile && <p className="recruitment-empty-note">Esta persona todavía no tiene un perfil estructurado disponible. Puedes revisar sus respuestas y el historial.</p>}
    </div>
    {!closed ? <footer className="applicant-decision"><label>Etapa de destino<select className="field-control" value={nextStage} disabled={busy || !stages.length} onChange={(event) => onNextStage(event.target.value)}><option value="">{stages.length ? "Elige una etapa" : "Configura una etapa de revisión"}</option>{stages.map((stage) => <option key={stage.id} value={stage.id}>{stage.title}</option>)}</select></label><div><button type="button" className="button-secondary applicant-reject" disabled={busy} onClick={onReject}>Finalizar con feedback</button><button type="button" className="button-primary" disabled={busy || !nextStage || loading} onClick={onAdvance}>{busy ? "Guardando…" : "Cambiar etapa"}<ArrowRight size={16} /></button></div>{onHire && <button className="button-ghost applicant-hire" disabled={busy || loading} onClick={onHire}>Confirmar contratación</button>}</footer> : <footer className="applicant-closed">Proceso finalizado · Consulta sus comunicaciones en el historial.</footer>}
  </aside>;
}
