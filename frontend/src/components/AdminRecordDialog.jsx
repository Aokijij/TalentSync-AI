import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardCheck, ExternalLink, CheckCircle2, CircleAlert, RefreshCw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { CoachDialog } from "./CoachDialog.jsx";
import { AdminVacancyActions } from "./AdminVacancyActions.jsx";
import { ExternalVacancyStatus } from "./ExternalVacancyStatus.jsx";
import { EDUCATION_LEVELS } from "../constants/educationLevels.js";
import { skillName } from "../utils/skillNames.js";
import "../styles/admin-records.css";

const statusLabels = { active: "Activa", draft: "Borrador", paused: "Pausada", closed: "Cerrada", filled: "Cubierta", automatic: "Revisión automática", approved: "Aprobada por administración", held: "Retirada del catálogo", pending: "Pendiente", verified: "Verificada", rejected: "Rechazada", candidate: "Candidato", company: "Empresa", admin: "Administrador", remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial", full_time: "Tiempo completo", part_time: "Tiempo parcial", indefinite: "Indefinido", fixed_term: "Término fijo", service: "Prestación de servicios", internship: "Práctica", temporary: "Temporal", freelance: "Independiente" };
const label = (value) => statusLabels[value] || value || "Sin registrar";
const date = (value) => value ? new Date(value.endsWith("Z") ? value : value + "Z").toLocaleString("es-CO") : "Sin registrar";
const money = (value) => value ? new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value) : "No informado";
function safeUrl(value) { try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password ? url.href : ""; } catch { return ""; } }

export function AdminRecordDialog({ record, onClose, onChanged, onSelect }) {
  const [data, setData] = useState(null), [error, setError] = useState(""), [busy, setBusy] = useState(false), [reload, setReload] = useState(0), [notice, setNotice] = useState("");
  const [decision, setDecision] = useState("automatic"), [note, setNote] = useState("");
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError(""); setNotice("");
    api.get(`/admin/${record.kind}/${record.id}${record.kind === "jobs" ? "/review" : ""}`, { signal: controller.signal, __skipRetry: true }).then(({ data }) => {
      if (!controller.signal.aborted) { setData(data); setDecision(data.moderation_status || "automatic"); setNote(data.moderation_note || ""); }
    }).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure)); });
    return () => controller.abort();
  }, [record.kind, record.id, reload]);
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      const { data: updated } = await api.patch(`/admin/jobs/${record.id}/review`, { status: decision, note: note.trim(), revision: data.moderation_revision }, { __skipRetry: true });
      setData(updated); setNotice("Decisión editorial guardada. La próxima sincronización conservará esta revisión."); await onChanged();
    } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  const title = record.kind === "jobs" ? "Revisar vacante" : record.kind === "companies" ? "Ficha de empresa" : "Ficha de cuenta";
  return <CoachDialog open title={title} Icon={ClipboardCheck} className="admin-record-dialog" onClose={onClose} closeDisabled={busy}>
    <div className="admin-record-body">
      {!data && !error && <p role="status">Cargando información del registro…</p>}
      {error && <div role="alert" className="admin-record-error">{error}{!data && <button className="button-secondary" onClick={() => setReload((value) => value + 1)}>Reintentar</button>}{data && <button type="button" className="button-secondary button-sm" disabled={busy} onClick={() => setReload((value) => value + 1)}>Actualizar ficha<RefreshCw size={14} /></button>}</div>}
      {notice && <p role="status" className="admin-record-success">{notice}</p>}
      {data && <>
        <div className="admin-record-heading"><p className="section-kicker">{record.kind === "jobs" ? data.source_kind === "external" ? "CATÁLOGO EXTERNO" : "OFERTA TALENTSYNC" : "INFORMACIÓN ADMINISTRATIVA"}</p><h3>{data.title || data.name}</h3><p>{data.company_name || data.profile?.profession || data.sector || "Registro de la plataforma"}</p></div>
        {record.kind === "jobs" ? <>
          <dl className="admin-record-facts"><Fact title="Estado de la oferta" value={label(data.status)} /><Fact title="Salario mensual" value={data.quality_details?.salary_max > data.salary ? `${money(data.salary)} – ${money(data.quality_details.salary_max)}` : money(data.salary)} /><Fact title="Ubicación" value={[data.location, data.department].filter(Boolean).join(" · ")} /><Fact title="Modalidad" value={label(data.modality)} /><Fact title="Dedicación" value={label(data.employment_type)} /><Fact title="Contrato" value={label(data.quality_details?.contract_type)} /><Fact title="Jornada" value={data.quality_details?.schedule} /><Fact title="Postulaciones en TalentSync" value={data.source_kind === "external" ? "Proceso en el portal de origen" : data.applications_count} /><Fact title="Publicación original" value={date(data.external_published_at || data.created_at)} /><Fact title="Vencimiento" value={date(data.expires_at)} /><Fact title="Fuente" value={data.source_portal || "TalentSync"} /></dl>
          <div className="admin-record-copy-grid"><Copy title="Funciones y descripción" text={data.description} /><Copy title="Requisitos de la oferta" text={data.requirements} /></div>
          <section className="admin-record-section"><h4>Habilidades y condiciones</h4><Skills values={data.skills} /><p>{(data.benefits || []).join(" · ") || "Sin beneficios informados"}</p>{!!data.languages?.length && <p>Idiomas: {data.languages.map((row) => `${row.name || row.language} · ${row.level}`).join(", ")}</p>}<p>Formación: {EDUCATION_LEVELS[data.required_education_level] || data.required_education_level || "No estructurada"} · {(data.required_study_fields || []).join(", ") || "Revisa el texto de requisitos"}</p></section>
          <section className="admin-publication-review"><header><div><h4>Revisión para publicar</h4><p>Contrasta los puntos pendientes con el contenido y la fuente.</p></div><span data-ready={data.review?.can_publish}>{data.review?.can_publish ? "Cumple los controles" : "Hay puntos pendientes"}{data.review?.score != null ? ` · ${data.review.score}/100` : ""}</span></header><ul>{data.review?.checks.map((row, index) => <li key={index}>{row.passed ? <CheckCircle2 size={17} /> : <CircleAlert size={17} />}<span>{row.label}</span></li>)}</ul></section>
          {data.source_kind === "external" ? <>
            <ExternalVacancyStatus key={`${data.id}-${data.moderation_revision}`} job={data} admin />
            {safeUrl(data.external_url) && <a className="button-secondary" href={safeUrl(data.external_url)} target="_blank" rel="noopener noreferrer">Consultar oferta original<ExternalLink size={16} /></a>}
            <form className="admin-editorial-form" onSubmit={save}><div><h4>Estado en el catálogo de TalentSync</h4><p>La aprobación conserva los controles automáticos de vigencia y claridad. Retirar una oferta la oculta del catálogo y de las recomendaciones.</p></div><label>Decisión editorial<select className="field-control" value={decision} onChange={(event) => setDecision(event.target.value)} disabled={busy}><option value="automatic">Revisión automática</option><option value="approved" disabled={!data.review?.can_publish}>Aprobar publicación</option><option value="held">Retirar del catálogo</option></select></label><label>Motivo de la decisión<textarea className="field-control" rows={3} minLength={5} maxLength={2000} required value={note} onChange={(event) => setNote(event.target.value)} disabled={busy} /></label><button type="submit" className="button-primary" disabled={busy || note.trim().length < 5}>{busy ? "Guardando…" : "Guardar decisión"}</button><small>Estado actual: {label(data.moderation_status)}. Se conserva el historial y el registro original.</small></form>
          </> : <AdminVacancyActions key={data.id} job={data} allowDelete={false} onChanged={async () => { await onChanged(); setReload((value) => value + 1); }} />}
          <details className="admin-record-history"><summary>Historial de cambios ({data.history?.length || 0})</summary>{data.history?.length ? <ol>{data.history.map((row) => <li key={row.id}><strong>{row.event === "job.publication_reviewed" ? "Revisión editorial" : row.event === "job.status_updated" ? "Cambio de estado" : "Actualización de la oferta"}</strong><span>{date(row.created_at)}{row.details?.status ? ` · ${label(row.details.status)}` : ""}</span></li>)}</ol> : <p>No hay cambios registrados para esta oferta.</p>}</details>
        </> : record.kind === "users" ? <>
          <dl className="admin-record-facts"><Fact title="Correo de acceso" value={data.email} /><Fact title="Rol" value={label(data.role)} /><Fact title="Registro" value={date(data.created_at)} /><Fact title="Correo confirmado" value={data.email_verified ? "Sí" : "No"} /><Fact title="Verificación en dos pasos" value={data.mfa_enabled ? "Activada" : "Sin activar"} /><Fact title="Estado de la cuenta" value={data.registration_pending ? "Registro por completar" : "Registro completado"} /></dl>
          {data.profile && <section className="admin-record-section"><h4>Trayectoria registrada</h4><Copy text={data.profile.summary} /><Skills values={data.profile.skills} /><dl className="admin-record-facts"><Fact title="Ubicación" value={[data.profile.location, data.profile.department].filter(Boolean).join(" · ")} /><Fact title="Experiencias" value={data.profile.experiences_count} /><Fact title="Formaciones" value={data.profile.educations_count} /><Fact title="Cursos y certificados" value={data.profile.certifications_count} /><Fact title="Idiomas" value={data.profile.languages?.length || 0} /><Fact title="Hoja de vida aportada" value={data.profile.has_cv ? "Sí" : "No"} /></dl></section>}
          <JobLinks title="Postulaciones recientes" rows={data.applications} onSelect={onSelect} applications />
        </> : <>
          <dl className="admin-record-facts"><Fact title="Tipo de registro" value={data.is_external ? "Empresa identificada en fuentes externas" : "Organización de TalentSync"} /><Fact title="Verificación" value={data.is_external ? "No aplica al catálogo externo" : label(data.verification_status)} /><Fact title="Ubicación" value={data.location} /><Fact title="Sector" value={data.sector} /><Fact title="Vacantes registradas" value={data.jobs_count} /><Fact title="Correo del responsable" value={data.owner_email} /></dl><Copy title="Acerca de la empresa" text={data.description} /><Copy title="Propósito" text={data.mission} />{safeUrl(data.website) && <a className="button-secondary" href={safeUrl(data.website)} target="_blank" rel="noopener noreferrer">Sitio de la empresa<ExternalLink size={16} /></a>}{!data.is_external && <Link className="button-secondary" to="/admin/verificaciones">Gestionar verificación</Link>}<JobLinks title="Vacantes de esta organización" rows={data.jobs} onSelect={onSelect} />
        </>}
      </>}
    </div>
  </CoachDialog>;
}

function Fact({ title, value }) { return <div><dt>{title}</dt><dd>{value === 0 ? "0" : value || "Sin registrar"}</dd></div>; }
function Copy({ title, text }) { return <section className="admin-record-section">{title && <h4>{title}</h4>}<p className="admin-record-text">{text || "Sin información aportada"}</p></section>; }
function Skills({ values }) { return <div className="admin-record-skills">{values?.length ? values.map((value) => <span key={value}>{skillName(value)}</span>) : <p>Sin habilidades registradas</p>}</div>; }
function JobLinks({ title, rows, onSelect, applications = false }) { return <section className="admin-record-section"><h4>{title}</h4>{rows?.length ? <ul className="admin-record-links">{rows.map((row) => <li key={row.id}><button type="button" onClick={() => onSelect({ kind: "jobs", id: applications ? row.job_id : row.id })}>{row.job_title || row.title}</button><span>{label(row.status)}{applications ? ` · ${date(row.created_at)}` : ` · ${row.applications_count} postulaciones`}</span></li>)}</ul> : <p>No hay registros en esta sección.</p>}</section>; }
