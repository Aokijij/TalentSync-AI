import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Mail, Plus, Search, Settings2, ShieldCheck, UsersRound, X } from "lucide-react";
import { api } from "../api/client.js";
import { useDebouncedValue, usePagedList } from "../hooks/usePagedList.js";

const ROLES = { recruiter: "Reclutador", interviewer: "Entrevistador" };
const INVITATION_STATUS = { pending: "Pendiente", accepted: "Aceptada", expired: "Vencida o cancelada" };
const PAGE_SIZE = 6;
const initials = (name) => name.trim().split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();

export function TeamManagement({ jobs, busy: saving, act, canInvite, mfaRequired, localMail = false, refresh = 0, onCount }) {
  const [view, setView] = useState("members");
  const [query, setQuery] = useState(""), [status, setStatus] = useState("all"), [page, setPage] = useState(1);
  const [editor, setEditor] = useState(null);
  const search = useDebouncedValue(query);
  const { data, loading, error, reload } = usePagedList("/organization/team-page", { kind: view, status, search, page, page_size: PAGE_SIZE }, refresh);
  const counts = data?.counts || {};
  const active = counts.active || 0, pending = counts.pending || 0;
  const total = data?.total || 0, memberCount = counts.members || 0, invitationCount = counts.invitations || 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE)), currentPage = data?.page || 1;
  const visible = data?.items || [];
  const busy = saving || loading || search !== query.trim();
  useEffect(() => { onCount?.(memberCount); }, [memberCount, onCount]);
  function changeView(value) { setView(value); setStatus("all"); setQuery(""); setPage(1); setEditor(null); }
  async function save(values) {
    const success = await act(() => editor.kind === "invite"
      ? api.post("/organization/invitations", { email: values.email, role: values.role, assigned_job_ids: values.assigned_job_ids })
      : api.patch(`/organization/team/${editor.member.id}`, { role: values.role, active: values.active, assigned_job_ids: values.assigned_job_ids }));
    if (success) { if (editor.kind === "invite") { setView("invitations"); setStatus("all"); setQuery(""); setPage(1); } setEditor(null); }
  }
  return <section className="surface-card team-workspace">
    <header className="team-header">
      <div className="team-heading"><span className="team-heading-icon"><UsersRound size={22} /></span><div><h2>Tu equipo de contratación</h2><p>Gestiona personas, permisos y procesos desde un solo lugar.</p></div></div>
      <button type="button" className="button-primary" disabled={busy || !!editor || !canInvite} onClick={() => setEditor({ kind: "invite" })}><Plus size={17} />Invitar integrante</button>
    </header>
    <div className="team-overview"><span><i className="team-dot active" />{active} {active === 1 ? "activo" : "activos"}</span><span><i className="team-dot" />{counts.revoked || 0} con acceso retirado</span><span><Mail size={14} />{pending} {pending === 1 ? "invitación pendiente" : "invitaciones pendientes"}</span></div>
    <p className="team-invite-note">El registro de empresa crea al propietario. Para sumar un reclutador o entrevistador, invita su correo y elige su permiso aquí. Al pulsar «Preparar invitación», se genera un enlace personal para ese correo. El invitado lo abre, inicia sesión o crea su cuenta y acepta incorporarse a tu empresa. No debe registrar otra empresa.</p>
    {localMail && <div className="team-local-invitation"><Mail size={20} /><div><strong>¿Dónde está el enlace de invitación?</strong><p>En esta versión local, abre la bandeja de correo después de preparar la invitación. Busca el correo del integrante y pulsa «Abrir invitación al equipo». No se envían correos reales.</p><Link className="button-secondary button-sm" to="/desarrollo/correos">Ver invitaciones en la bandeja local</Link></div></div>}
    <details className="team-permissions-help"><summary><ShieldCheck size={15} />Qué puede hacer cada rol</summary><div><p><strong>Propietario</strong>Administra verificación, equipo, empresa y contratación.</p><p><strong>Reclutador</strong>Gestiona las vacantes y candidaturas de la empresa. No administra el equipo.</p><p><strong>Entrevistador</strong>Consulta procesos asignados y guarda evaluaciones internas. No publica ofertas ni cambia decisiones de contratación.</p></div></details>
    {editor?.kind === "invite" && <TeamEditor key="invite" jobs={jobs} busy={busy} mfaRequired={mfaRequired} localMail={localMail} onSave={save} onClose={() => setEditor(null)} />}
    <div className="team-list-toolbar">
      <nav aria-label="Listas del equipo" className="team-list-tabs"><button type="button" aria-pressed={view === "members"} disabled={busy || !!editor} onClick={() => changeView("members")}>Integrantes <span>{memberCount}</span></button><button type="button" aria-pressed={view === "invitations"} disabled={busy || !!editor} onClick={() => changeView("invitations")}>Invitaciones <span>{invitationCount}</span></button></nav>
      <div className="team-filters"><label className="team-search"><Search size={16} /><input className="field-control" aria-label="Buscar en el equipo" maxLength={120} placeholder="Nombre, correo o rol" value={query} disabled={!!editor} onChange={(event) => { setQuery(event.target.value); setPage(1); }} /></label><select className="field-control" aria-label="Filtrar estado del equipo" value={status} disabled={!!editor} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="all">Todos los estados</option>{view === "members" ? <><option value="active">Acceso activo</option><option value="revoked">Acceso retirado</option></> : <><option value="pending">Pendientes</option><option value="accepted">Aceptadas</option><option value="expired">Vencidas o canceladas</option></>}</select></div>
    </div>
    {error && <p role="alert" className="offer-alert error">{error}<button type="button" className="button-secondary button-sm" onClick={reload}>Reintentar</button></p>}
    <div className="team-list" aria-busy={busy}>
      {loading && <p role="status" className="p-4 text-sm text-[var(--muted)]">Cargando equipo…</p>}
      {!busy && !error && !visible.length && <div className="team-empty"><UsersRound size={28} /><h3>{query || status !== "all" ? "No hay coincidencias" : view === "members" ? "Tu equipo comienza aquí" : "Sin invitaciones"}</h3><p>{query || status !== "all" ? "Prueba con otro nombre, correo o estado." : view === "members" ? "Invita a un reclutador o entrevistador para trabajar juntos." : "Las invitaciones que prepares aparecerán en esta lista."}</p></div>}
      {visible.map((row) => <article key={row.id} className={`team-member ${editor?.member?.id === row.id ? "is-editing" : ""}`}>
        <div className="team-member-row"><span className="team-avatar" aria-hidden="true">{view === "members" ? initials(row.name || row.email) : <Mail size={19} />}</span><div className="team-member-identity"><h3>{row.name || row.email}</h3>{row.name && <p>{row.email}</p>}<small>{view === "members" ? row.role === "recruiter" ? "Gestiona todas las vacantes" : `${row.assigned_job_ids.length} ${row.assigned_job_ids.length === 1 ? "vacante asignada" : "vacantes asignadas"}` : `Vence ${new Date(row.expires_at + "Z").toLocaleDateString("es-CO")}`}</small></div><span className="team-role">{ROLES[row.role]}</span><span className={`team-status ${(view === "members" ? row.active : row.status === "accepted") ? "active" : ""}`}>{view === "members" ? row.active ? "Activo" : "Acceso retirado" : INVITATION_STATUS[row.status]}</span>{view === "members" ? <button type="button" className="button-secondary button-sm" disabled={busy || !!editor} aria-label={`Gestionar permisos de ${row.name}`} onClick={() => setEditor({ kind: "edit", member: row })}><Settings2 size={15} />Gestionar</button> : row.status === "pending" ? <button type="button" className="button-secondary button-sm" disabled={busy || !!editor} onClick={() => act(() => api.delete(`/organization/invitations/${row.id}`))}>Cancelar invitación</button> : null}</div>
        {view === "members" && editor?.member?.id === row.id && <TeamEditor key={row.id} member={row} jobs={jobs} busy={busy} mfaRequired={mfaRequired} localMail={localMail} onSave={save} onClose={() => setEditor(null)} />}
      </article>)}
    </div>
    {!!total && <footer className="team-list-footer"><p>{(currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, total)} de {total} {view === "members" ? total === 1 ? "integrante" : "integrantes" : total === 1 ? "invitación" : "invitaciones"}</p>{pages > 1 && <nav aria-label="Paginación del equipo"><button type="button" className="button-secondary button-sm" aria-label="Página anterior del equipo" disabled={busy || !!editor || currentPage === 1} onClick={() => setPage(currentPage - 1)}><ChevronLeft size={16} /></button><span>{currentPage} / {pages}</span><button type="button" className="button-secondary button-sm" aria-label="Página siguiente del equipo" disabled={busy || !!editor || currentPage === pages} onClick={() => setPage(currentPage + 1)}><ChevronRight size={16} /></button></nav>}</footer>}
  </section>;
}

function TeamEditor({ member, jobs, busy, mfaRequired, localMail, onSave, onClose }) {
  const [role, setRole] = useState(member?.role || "recruiter");
  const [selected, setSelected] = useState(member?.assigned_job_ids || []);
  const [active, setActive] = useState(member?.active ?? true);
  const [query, setQuery] = useState("");
  const matches = jobs.filter((job) => job.title.toLowerCase().includes(query.trim().toLowerCase()));
  return <form className="team-editor" aria-label={member ? `Permisos de ${member.name}` : "Invitar a una persona"} onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); onSave({ email: data.get("email"), role, active, assigned_job_ids: selected }); }}>
    <header><div><h3>{member ? "Editar permisos" : "Invitar a una persona"}</h3><p>{member ? "Los cambios se aplicarán cuando guardes." : "Elige cómo participará en tu equipo."}</p></div><button className="button-ghost" type="button" aria-label="Cerrar editor del equipo" disabled={busy} onClick={onClose}><X size={18} /></button></header>
    {!member && <label className="team-email">Correo del integrante<input autoFocus className="field-control" name="email" type="email" required disabled={busy} placeholder="nombre@empresa.com" /></label>}
    <fieldset className="team-role-picker" disabled={busy}><legend>Permiso</legend>{Object.entries(ROLES).map(([value, label]) => <label key={value} className={role === value ? "selected" : ""}><input autoFocus={!!member && role === value} type="radio" name="role" value={value} checked={role === value} onChange={() => setRole(value)} /><span><strong>{label}</strong><small>{value === "recruiter" ? "Vacantes y candidaturas de la empresa" : "Procesos asignados y evaluaciones internas"}</small></span></label>)}</fieldset>
    {role === "interviewer" ? <fieldset className="team-assignment-picker" disabled={busy}><legend>Vacantes asignadas <span>{selected.length} {selected.length === 1 ? "seleccionada" : "seleccionadas"}</span></legend><label className="team-search"><Search size={16} /><input className="field-control" aria-label="Buscar vacantes para asignar" placeholder="Buscar por nombre del cargo" value={query} onChange={(event) => setQuery(event.target.value)} /></label><div className="team-assignment-list">{matches.map((job) => <label key={job.id}><input type="checkbox" checked={selected.includes(job.id)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, job.id] : current.filter((id) => id !== job.id))} /><span>{job.title}<small>{job.status === "draft" ? "Borrador" : job.status === "active" ? "Activa" : "Cerrada / pausada"}</small></span></label>)}{!matches.length && <p>{jobs.length ? "No hay vacantes con ese nombre." : "Crea una vacante para poder asignarla."}</p>}</div><p>Solo podrá consultar y evaluar los procesos de las vacantes seleccionadas.</p></fieldset> : <p className="team-role-note"><ShieldCheck size={17} />El reclutador gestiona todas las vacantes de la empresa; no necesita asignación individual.</p>}
    {member && <label className={`team-access-toggle ${!active ? "revoked" : ""}`}><input type="checkbox" checked={active} disabled={busy} onChange={(event) => setActive(event.target.checked)} /><span><strong>Mantener acceso activo</strong><small>{active ? "Puede acceder con los permisos seleccionados." : "Al guardar, perderá el acceso a la organización y sus procesos."}</small></span></label>}
    {!member && <p className="team-invite-note">La invitación vence en tres días. El destinatario confirma su correo{mfaRequired ? " y configura MFA" : ""} antes de aceptar. {localMail ? <>Después de preparar la invitación, encontrarás su enlace en la <Link to="/desarrollo/correos">bandeja local de correo</Link>.</> : "Recibirá un correo con el enlace personal para unirse al equipo."}</p>}
    <footer><button type="button" className="button-secondary" disabled={busy} onClick={onClose}>Cancelar</button><button className="button-primary" disabled={busy}>{busy ? "Guardando…" : member ? "Guardar permisos" : "Preparar invitación"}</button></footer>
  </form>;
}
