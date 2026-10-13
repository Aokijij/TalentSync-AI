import { InterviewAssignmentManager } from "../components/InterviewAssignmentManager.jsx";
import { Building2, CheckCircle2, ClipboardList, ShieldCheck, UsersRound } from "lucide-react";
import { CompanyVerificationForm } from "../components/CompanyVerificationForm.jsx";
import { TeamManagement } from "../components/TeamManagement.jsx";
import { AssignedInterviews } from "../components/AssignedInterviews.jsx";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { PageHeader } from "../components/PageHeader.jsx";

const statuses = { pending: "Sin presentar", reviewing: "En revisión", information_required: "Correcciones solicitadas", verified: "Verificada", rejected: "Rechazada", suspended: "Suspendida" };
const roles = { owner: "Propietario", recruiter: "Reclutador", interviewer: "Entrevistador" };

export function OrganizationWorkspace() {
  const { user, accessOptions } = useAuth();
  const [organization, setOrganization] = useState(null), [teamCount, setTeamCount] = useState(0), [teamRefresh, setTeamRefresh] = useState(0), [jobs, setJobs] = useState([]), [assignments, setAssignments] = useState([]);
  const [tab, setTab] = useState(({ "#equipo": "team", "#procesos": "assignments", "#asignar": "dispatch", "#verificacion": "verification" })[window.location.hash] || ""), [error, setError] = useState(""), [message, setMessage] = useState(""), [busy, setBusy] = useState(false);
  async function load() {
    const { data } = await api.get("/organization/me"); setOrganization(data); setTab((current) => data.role === "interviewer" ? "assignments" : current || (data.verification_status === "verified" ? data.role === "owner" ? "team" : "assignments" : "verification"));
    if (["owner", "recruiter"].includes(data.role)) {
      const c = data.verification_status === "suspended" ? { data: [] } : await api.get("/jobs", { params: { status: "" } });
      setJobs(c.data.filter((job) => job.company_id === data.id));

    }
    if (!data.verification_required || data.verification_status === "verified") setAssignments((await api.get("/organization/assignments")).data);
    else setAssignments([]);
  }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function act(action) { setBusy(true); setError(""); setMessage(""); try { const result = await action(); await load(); setTeamRefresh((value) => value + 1); setMessage(result?.data?.message || "Cambios guardados"); return true; } catch (failure) { setError(getApiErrorMessage(failure)); return false; } finally { setBusy(false); } }
  const verified = organization?.verification_status === "verified";
  return <div className="organization-workspace space-y-5"><PageHeader kicker="Administración de empresa" title={organization?.role === "interviewer" ? "Tu espacio de entrevistas" : "Organización y equipo"} description={organization?.role === "interviewer" ? "Consulta las candidaturas asignadas y comparte con el equipo una evaluación basada en evidencias." : verified ? "Coordina al equipo, distribuye entrevistas y sigue tus procesos de selección." : "Prepara la organización y completa los pasos para empezar a contratar."} />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{message && <p role="status" className="surface-card p-4">{message}</p>}
    {!organization && !error && <p>Cargando organización…</p>}
    {organization && <><section className="surface-card organization-identity"><span className="organization-symbol"><Building2 size={26} /></span><div><h2>{organization.name}</h2><p>{roles[organization.role]} · <span className={verified ? "text-[var(--success)]" : ""}>{statuses[organization.verification_status]}</span></p></div><Link className="button-secondary button-sm" to="/seguridad">Seguridad de mi acceso</Link></section>
    <nav className="workspace-tabs organization-tabs" aria-label="Administración de organización">{[...(!verified ? [["verification", "Verificación", ShieldCheck]] : []), ...(organization.role === "owner" ? [["team", `Equipo${teamCount ? ` (${teamCount})` : ""}`, UsersRound]] : []), ["assignments", "Procesos asignados", ClipboardList], ...(["owner", "recruiter"].includes(organization.role) && verified ? [["dispatch", "Asignar entrevistas", UsersRound]] : []), ...(verified ? [["verification", "Verificada", CheckCircle2]] : [])].map(([value, label, Icon]) => <button key={value} className={tab === value ? "active" : ""} aria-pressed={tab === value} onClick={() => setTab(value)}><Icon size={17} />{label}</button>)}</nav>
    {tab === "verification" && <section className="surface-card space-y-5 p-5"><header className="verification-heading"><span className="organization-symbol"><ShieldCheck size={28} /></span><div><p className="section-kicker">Estado de la organización</p><h2>{verified ? "Verificación completada" : "Prepara tu empresa para contratar"}</h2><p>{verified ? "Consulta aquí el estado y la respuesta de la revisión." : "Completa la solicitud con datos y soportes de tu organización."}</p></div></header><ol className="grid gap-3 md:grid-cols-3">{[["Correo confirmado", user.email_verified], [accessOptions?.company_mfa_required === false ? "Autenticador opcional en revisión local" : "Autenticador activo", user.mfa_enabled || accessOptions?.company_mfa_required === false], ["Organización verificada", verified]].map(([label, done], index) => <li className="rounded-xl border border-[var(--line)] p-4" key={label}><p className="text-xs text-[var(--muted)]">Paso {index + 1}</p><p className="mt-2 font-semibold">{done ? "✓" : "Pendiente"} · {label}</p></li>)}</ol>
      {organization.feedback && <div className="rounded-xl bg-[var(--surface-subtle)] p-4"><h3 className="font-semibold">Respuesta de la revisión</h3><p className="mt-2 text-sm">{organization.feedback}</p></div>}
      {verified ? <p>La empresa está verificada. Puedes publicar ofertas y gestionar candidaturas.</p> : <p className="text-sm text-[var(--muted)]">Prepara ofertas en borrador mientras se revisa la organización. La revisión local es manual; no consulta registros oficiales automáticamente.</p>}
      {organization.verification_status === "reviewing" && <p role="status" className="rounded-xl border border-[var(--line)] p-4 text-sm">Solicitud presentada. Espera la decisión del administrador. Puedes actualizarla si necesitas corregir algún dato.</p>}
      {organization.role !== "owner" && <p>El propietario presenta y corrige los datos de verificación.</p>}
      {organization.role === "owner" && organization.verification_status !== "verified" && <CompanyVerificationForm key={organization.id} organization={organization} user={user} busy={busy} act={act} />}

    </section>}
    {tab === "team" && organization.role === "owner" && <TeamManagement refresh={teamRefresh} onCount={setTeamCount} jobs={jobs} busy={busy} act={act} canInvite={user.email_verified} mfaRequired={accessOptions?.company_mfa_required !== false} />}
    {tab === "dispatch" && verified && ["owner", "recruiter"].includes(organization.role) && <InterviewAssignmentManager jobs={jobs} busy={busy} act={act} />}
    {tab === "assignments" && <AssignedInterviews assignments={assignments} />}
    </>}
  </div>;
}
