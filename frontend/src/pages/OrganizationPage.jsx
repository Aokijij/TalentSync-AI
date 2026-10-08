import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { useAuth } from "../hooks/useAuth.js";

const labels = { pending: "Pendiente", reviewing: "En revisión", information_required: "Falta información", verified: "Verificada", rejected: "Rechazada", suspended: "Suspendida" };
const jobIds = (value) => value.split(",").map(Number).filter((id) => Number.isInteger(id) && id > 0);

export function OrganizationPage() {
  const [organization, setOrganization] = useState(null);
  const [members, setMembers] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    const { data } = await api.get("/organization/me"); setOrganization(data);
    if (data.role === "owner") setMembers((await api.get("/organization/team")).data);
    if (!data.verification_required || data.verification_status === "verified") setAssignments((await api.get("/organization/assignments")).data);
  }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function act(action) { setBusy(true); setError(""); setMessage(""); try { const result = await action(); setMessage(result?.data?.message || "Cambios guardados"); await load(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }
  return <div className="space-y-5"><PageHeader kicker="Empresa" title="Verificación y equipo" description="Acredita tu organización y concede acceso según el trabajo de cada persona." />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{message && <p role="status" className="surface-card p-4">{message}</p>}
    {!organization && !error && <p>Cargando organización…</p>}
    {organization && <><section className="surface-card space-y-3 p-5"><h2 className="text-xl font-bold">{organization.name}</h2><p>Tu permiso: {organization.role === "owner" ? "Propietario" : organization.role === "recruiter" ? "Reclutador" : "Entrevistador"}</p><p>Verificación: {organization.verification_required ? labels[organization.verification_status] : "Cuenta existente; revisión disponible"}</p>{organization.feedback && <p className="rounded-lg bg-[var(--surface-subtle)] p-3">{organization.feedback}</p>}<Link className="text-[var(--accent)]" to="/seguridad">Confirmar correo y gestionar seguridad</Link>
      {organization.role === "owner" && !["verified", "suspended"].includes(organization.verification_status) && <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget)); if (!data.website) delete data.website; act(() => api.post("/organization/verification", data)); }}>
        <label>Razón social<input className="field-control mt-1" name="legal_name" minLength={3} maxLength={180} required defaultValue={organization.submission?.legal_name || organization.name} /></label>
        <label>Sitio web (opcional)<input className="field-control mt-1" name="website" type="url" defaultValue={organization.submission?.website || ""} /></label>
        <label>Referencia del registro mercantil<input className="field-control mt-1" name="registry_reference" minLength={5} maxLength={300} required defaultValue={organization.submission?.registry_reference || ""} /></label>
        <label>Cargo del representante<input className="field-control mt-1" name="representative_role" minLength={3} maxLength={120} required defaultValue={organization.submission?.representative_role || ""} /></label>
        <label className="sm:col-span-2">Información para la revisión<textarea className="field-control mt-1" name="notes" maxLength={1500} defaultValue={organization.submission?.notes || ""} /></label>
        <p className="text-sm text-[var(--muted)] sm:col-span-2">Un administrador revisará estos datos. Mientras tanto puedes preparar vacantes en borrador.</p><button disabled={busy} className="button-primary">Enviar a revisión</button>
      </form>}
    </section>
    {organization.role === "owner" && <section className="surface-card space-y-4 p-5"><h2 className="font-bold">Invitar al equipo</h2><form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget)); act(() => api.post("/organization/invitations", { ...data, assigned_job_ids: jobIds(data.assigned_job_ids) })); }}><label>Correo de la persona<input className="field-control mt-1" name="email" type="email" required /></label><label>Permiso<select className="field-control mt-1" name="role"><option value="recruiter">Reclutador</option><option value="interviewer">Entrevistador</option></select></label><label>IDs de vacantes asignadas, separados por comas<input className="field-control mt-1" name="assigned_job_ids" placeholder="1, 2" /></label><button disabled={busy} className="button-primary self-end">Crear invitación local</button></form><p className="text-sm text-[var(--muted)]">Los reclutadores gestionan vacantes y postulaciones. Los entrevistadores consultan únicamente sus asignaciones. Solo el propietario administra el equipo.</p>
      {members.map((member) => <form key={member.id} className="grid gap-3 border-t border-[var(--line)] pt-4 sm:grid-cols-4" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(() => api.patch(`/organization/team/${member.id}`, { role: data.get("role"), active: data.get("active") === "on", assigned_job_ids: jobIds(data.get("assigned_job_ids")) })); }}><div><p className="font-semibold">{member.name}</p><p className="break-all text-xs">{member.email}</p></div><label>Permiso<select className="field-control" name="role" defaultValue={member.role}><option value="recruiter">Reclutador</option><option value="interviewer">Entrevistador</option></select></label><label>Vacantes<input className="field-control" name="assigned_job_ids" defaultValue={member.assigned_job_ids.join(", ")} /></label><div><label className="flex gap-2"><input name="active" type="checkbox" defaultChecked={member.active} />Acceso activo</label><button disabled={busy} className="button-secondary mt-2">Actualizar permisos</button></div></form>)}
    </section>}
    <section className="surface-card space-y-4 p-5"><h2 className="font-bold">Asignaciones de entrevistas</h2>{!assignments.length && <p className="text-sm text-[var(--muted)]">No hay asignaciones disponibles.</p>}{assignments.map((job) => <div key={job.job_id}><h3 className="font-semibold">#{job.job_id} · {job.title}</h3>{job.applications.map((row) => <p key={row.id} className="mt-2 text-sm">{row.candidate_alias} · {row.stage || "Recibida"} · {row.interview_at ? new Date(row.interview_at + "Z").toLocaleString("es-CO") : "Sin fecha de entrevista"}</p>)}</div>)}</section></>}
  </div>;
}

export function VerificationQueuePage() {
  const [rows, setRows] = useState([]); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function load() { setRows((await api.get("/admin/verifications")).data); }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  return <div className="space-y-5"><PageHeader kicker="Administración" title="Verificación de empresas" description="Revisa la evidencia presentada, solicita correcciones y registra una decisión motivada." />{error && <p role="alert">{error}</p>}{!rows.length && <p>No hay solicitudes.</p>}{rows.map((row) => <article className="surface-card space-y-3 p-5" key={row.id}><h2 className="font-bold">{row.name} · {labels[row.status]}</h2><p>NIT: {row.nit}</p><dl className="space-y-2 text-sm">{Object.entries(row.submission || {}).map(([key, value]) => <div key={key}><dt className="font-semibold">{{ legal_name: "Razón social", website: "Web", registry_reference: "Registro", representative_role: "Cargo", notes: "Notas", submitted_at: "Presentada" }[key] || key}</dt><dd className="break-all">{String(value)}</dd></div>)}</dl>{row.feedback && <p>{row.feedback}</p>}<form className="grid gap-3 sm:grid-cols-2" onSubmit={async (event) => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget)); setBusy(true); setError(""); try { await api.post(`/admin/verifications/${row.id}`, data); await load(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }}><label>Decisión<select className="field-control mt-1" name="status"><option value="information_required">Solicitar información</option><option value="verified">Aprobar</option><option value="rejected">Rechazar</option><option value="suspended">Suspender</option></select></label><label>Motivo<textarea className="field-control mt-1" name="feedback" minLength={10} maxLength={1500} required /></label><button className="button-primary" disabled={busy}>Guardar revisión</button></form></article>)}</div>;
}

export function InvitationPage() {
  const [params] = useSearchParams(); const token = params.get("token") || ""; const { user } = useAuth(); const location = useLocation(); const navigate = useNavigate();
  const [invitation, setInvitation] = useState(null); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { api.get("/organization/invitation", { params: { token } }).then(({ data }) => setInvitation(data)).catch((failure) => setError(getApiErrorMessage(failure))); }, [token]);
  return <main className="mx-auto max-w-xl p-6"><section className="surface-card space-y-4 p-6"><h1 className="text-2xl font-bold">Invitación a un equipo</h1>{error && <p role="alert">{error}</p>}{invitation && <><p>{invitation.company} te invita como {invitation.role === "interviewer" ? "entrevistador" : "reclutador"}.</p>{!user ? <div className="flex gap-3"><Link className="button-primary" to={`/empresa/registro?invitation=${encodeURIComponent(token)}`}>Crear cuenta</Link><Link className="button-secondary" state={{ from: location.pathname + location.search }} to="/empresa/login">Ya tengo cuenta</Link></div> : !user.email_verified || !user.mfa_enabled ? <Link className="button-primary inline-flex" to={`/seguridad?invitation=${encodeURIComponent(token)}`}>Confirmar correo y seguridad</Link> : <button disabled={busy} className="button-primary" onClick={async () => { setBusy(true); try { await api.post("/organization/invitations/accept", { token }); navigate("/empresa/equipo"); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }}>Aceptar con mi cuenta</button>}</>}</section></main>;
}
