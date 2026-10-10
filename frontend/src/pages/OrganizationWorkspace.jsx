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
  const [organization, setOrganization] = useState(null), [members, setMembers] = useState([]), [invitations, setInvitations] = useState([]), [jobs, setJobs] = useState([]), [assignments, setAssignments] = useState([]);
  const [tab, setTab] = useState(window.location.hash === "#equipo" ? "team" : "verification"), [error, setError] = useState(""), [message, setMessage] = useState(""), [busy, setBusy] = useState(false);
  async function load() {
    const { data } = await api.get("/organization/me"); setOrganization(data); if (data.role === "interviewer") setTab("assignments");
    if (data.role === "owner") {
      const [a, b, c] = await Promise.all([api.get("/organization/team"), api.get("/organization/invitations"), data.verification_status === "suspended" ? Promise.resolve({ data: [] }) : api.get("/jobs", { params: { status: "" } })]);
      setMembers(a.data); setInvitations(b.data); setJobs(c.data.filter((job) => job.company_id === data.id));
    }
    if (!data.verification_required || data.verification_status === "verified") setAssignments((await api.get("/organization/assignments")).data);
    else setAssignments([]);
  }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function act(action) { setBusy(true); setError(""); setMessage(""); try { const result = await action(); await load(); setMessage(result?.data?.message || "Cambios guardados"); return true; } catch (failure) { setError(getApiErrorMessage(failure)); return false; } finally { setBusy(false); } }
  const verified = organization?.verification_status === "verified";
  return <div className="space-y-5"><PageHeader kicker="Administración de empresa" title={organization?.role === "interviewer" ? "Tu espacio de entrevistas" : "Organización y equipo"} description={organization?.role === "interviewer" ? "Consulta las candidaturas asignadas y comparte con el equipo una evaluación basada en evidencias." : "Completa la verificación, administra los accesos y consulta los procesos asignados."} />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{message && <p role="status" className="surface-card p-4">{message}</p>}
    {!organization && !error && <p>Cargando organización…</p>}
    {organization && <><section className="surface-card flex flex-wrap items-center justify-between gap-4 p-5"><div><h2 className="text-xl font-bold">{organization.name}</h2><p className="mt-1 text-sm text-[var(--muted)]">{roles[organization.role]} · {statuses[organization.verification_status]}</p></div><Link className="button-secondary" to="/seguridad">Seguridad de mi acceso</Link></section>
    <nav className="flex flex-wrap gap-2" aria-label="Administración de organización">{[["verification", "Verificación"], ...(organization.role === "owner" ? [["team", `Equipo (${members.length})`]] : []), ["assignments", "Procesos asignados"]].map(([value, label]) => <button key={value} className={tab === value ? "button-primary" : "button-secondary"} aria-pressed={tab === value} onClick={() => setTab(value)}>{label}</button>)}</nav>
    {tab === "verification" && <section className="surface-card space-y-5 p-5"><h2 className="font-bold">Preparación de la empresa</h2><ol className="grid gap-3 md:grid-cols-3">{[["Correo confirmado", user.email_verified], [accessOptions?.company_mfa_required === false ? "Autenticador opcional en revisión local" : "Autenticador activo", user.mfa_enabled || accessOptions?.company_mfa_required === false], ["Organización verificada", verified]].map(([label, done], index) => <li className="rounded-xl border border-[var(--line)] p-4" key={label}><p className="text-xs text-[var(--muted)]">Paso {index + 1}</p><p className="mt-2 font-semibold">{done ? "✓" : "Pendiente"} · {label}</p></li>)}</ol>
      {organization.feedback && <div className="rounded-xl bg-[var(--surface-subtle)] p-4"><h3 className="font-semibold">Respuesta de la revisión</h3><p className="mt-2 text-sm">{organization.feedback}</p></div>}
      {verified ? <p>La empresa está verificada. Puedes publicar ofertas y gestionar candidaturas.</p> : <p className="text-sm text-[var(--muted)]">Prepara ofertas en borrador mientras se revisa la organización. La revisión local es manual; no consulta registros oficiales automáticamente.</p>}
      {organization.verification_status === "reviewing" && <p role="status" className="rounded-xl border border-[var(--line)] p-4 text-sm">Solicitud presentada. Espera la decisión del administrador. Puedes actualizarla si necesitas corregir algún dato.</p>}
      {organization.role !== "owner" && <p>El propietario presenta y corrige los datos de verificación.</p>}
      {organization.role === "owner" && organization.verification_status !== "verified" && <CompanyVerificationForm key={organization.id} organization={organization} user={user} busy={busy} act={act} />}

    </section>}
    {tab === "team" && organization.role === "owner" && <TeamManagement members={members} invitations={invitations} jobs={jobs} busy={busy} act={act} canInvite={user.email_verified} mfaRequired={accessOptions?.company_mfa_required !== false} />}
    {tab === "assignments" && <AssignedInterviews assignments={assignments} />}
    </>}
  </div>;
}
