import { ShieldCheck, Mail, LockKeyhole, Monitor, Eye } from "lucide-react";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { QRCodeSVG } from "qrcode.react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { SocialAccounts } from "../components/SocialAccounts.jsx";

export function SecurityPage() {
  const [params] = useSearchParams();
  const { confirm } = useFeedback();
  const { user, refreshUser, accessOptions, logout } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [privacy, setPrivacy] = useState(null);
  const [setup, setSetup] = useState(null);
  const [recovery, setRecovery] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try { const [a, b] = await Promise.all([api.get("/account/sessions"), user.role === "candidate" ? api.get("/account/privacy") : Promise.resolve({ data: null })]); setSessions(a.data); setPrivacy(b.data); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
  }
  useEffect(() => { load(); }, []);
  async function act(action) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <div className="security-page space-y-5">
    <PageHeader kicker="Tu cuenta" title={user.role === "candidate" ? "Seguridad y privacidad" : "Seguridad de cuenta"} description={user.role === "candidate" ? "Controla el acceso, las sesiones y cómo se comparten tus evidencias." : user.role === "admin" ? "Protege tu acceso administrativo y revisa tus dispositivos y sesiones." : "Administra tu correo, autenticador y sesiones. Los permisos del equipo se gestionan en Organización y equipo."} />
    <div className="security-overview">{[[Mail, "Correo", user.email_verified ? "Confirmado" : "Por confirmar"], [ShieldCheck, "Autenticador", user.mfa_enabled ? "Activo" : "Sin configurar"], [Monitor, "Sesiones", `${sessions.filter((row) => !row.revoked).length} abiertas`]].map(([Icon, title, detail]) => <article className="surface-card flex items-center gap-4 p-5" key={title}><span className="learning-area-icon"><Icon /></span><div><h2 className="text-sm text-[var(--muted)]">{title}</h2><p className="font-bold">{detail}</p></div></article>)}</div>
    <nav className="security-jump" aria-label="Secciones de seguridad">{[["email", "Correo"], ["mfa", "Autenticador"], ...(user.role === "candidate" ? [["privacy", "Privacidad"]] : []), ["sessions", "Dispositivos"]].map(([id, label]) => <a className="button-secondary" key={id} href={`#security-${id}`}>{label}</a>)}</nav>
    {user.role === "company" && accessOptions.company_mfa_required === false && !user.mfa_enabled && <div className="learning-published"><ShieldCheck /><p>El autenticador es opcional para empresas en este entorno de revisión. Puedes configurarlo cuando quieras.</p></div>}
    {user.role === "admin" && accessOptions.admin_mfa_required === false && <div className="learning-published"><ShieldCheck /><p>Revisión local: acceso administrativo sin segundo factor. Tu configuración del autenticador se conserva.</p></div>}
    {user.role === "candidate" && accessOptions.mode === "session" && <SocialAccounts user={user} providers={accessOptions.providers} onSessionsChanged={load} />}
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}
    {message && <p role="status" className="surface-card p-4">{message}</p>}
    {(user.role === "admin" && accessOptions.admin_mfa_required !== false || user.role === "company" && accessOptions.company_mfa_required !== false) && !user.mfa_enabled && <p className="surface-card p-4">Para operar como empresa o administrador, configura primero una aplicación autenticadora.</p>}
    <section id="security-email" className="surface-card security-section p-5"><h2 className="flex items-center gap-3 text-lg font-bold"><Mail size={21} className="text-[var(--accent)]" />Correo electrónico</h2><p className="mt-2">{user.email} · {user.email_verified ? "Confirmado" : "Pendiente de confirmar"}</p>
      {!user.email_verified && <button disabled={busy} className="button-secondary mt-3" onClick={() => act(async () => { const { data } = await api.post("/account/verify-email"); setMessage(data.message); })}>Enviar confirmación</button>}
      {accessOptions.local_mail && <Link className="ml-3 text-sm text-[var(--accent)]" to="/desarrollo/correos">Bandeja local</Link>}
      <form className="mt-4 grid gap-3 sm:grid-cols-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/change-email", { email: data.get("email"), password: data.get("password") }); setMessage(result.data.message); }); }}>
        <label className="text-sm">Nuevo correo<input className="field-control mt-1" name="email" required type="email" autoComplete="off" /></label>
        <label className="text-sm">Contraseña actual<input className="field-control mt-1" name="password" required type="password" autoComplete="current-password" /></label>
        <button disabled={busy} className="button-secondary self-end">Solicitar cambio</button>
      </form>
    </section>
    <section id="security-mfa" className="surface-card security-section p-5"><h2 className="flex items-center gap-3 text-lg font-bold"><LockKeyhole size={21} className="text-[var(--accent)]" />Autenticación de dos factores</h2><p className="mt-2 text-sm text-[var(--muted)]">{user.mfa_enabled ? "Activada. Puedes usar tu aplicación o un código de recuperación al ingresar." : "Añade la clave a una aplicación autenticadora y confirma con su código de seis dígitos."}</p>
      {!user.mfa_enabled && !setup && <form className="mt-4 flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/mfa/setup", { password: data.get("password") }); setSetup(result.data); }); }}>
        <label className="text-sm">Contraseña actual<input className="field-control mt-1" required name="password" type="password" autoComplete="current-password" /></label><button disabled={busy} className="button-primary self-end">Configurar autenticador</button>
      </form>}
      {setup && !user.mfa_enabled && <div className="mt-4 space-y-3"><ol className="list-inside list-decimal space-y-2 text-sm"><li>Abre tu aplicación autenticadora y elige añadir una cuenta.</li><li>Escanea este QR con la aplicación.</li><li>Escribe aquí el código de seis dígitos que muestra la aplicación.</li></ol><div className="inline-block rounded-xl bg-white p-4"><QRCodeSVG value={setup.uri} size={192} level="M" title="QR para configurar tu autenticador" /></div><details><summary className="cursor-pointer text-sm">¿No puedes escanear? Introducir clave manual</summary><code className="mt-2 block break-all rounded-lg bg-[var(--surface-subtle)] p-3">{setup.secret}</code></details>
        <form className="flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/mfa/confirm", { code: data.get("code") }); setRecovery(result.data.recovery_codes); setSetup(null); await refreshUser(); await load(); }); }}><label className="text-sm">Código del autenticador<input className="field-control mt-1" name="code" required pattern="[0-9]{6}" maxLength={6} placeholder="123456" title="Introduce los seis números de tu aplicación, no la clave de configuración" inputMode="numeric" autoComplete="one-time-code" /></label><button disabled={busy} className="button-primary self-end">Activar y obtener recuperación</button></form>
      </div>}
      {recovery.length > 0 && <div className="mt-4 rounded-lg border border-[var(--line)] p-4"><p className="font-semibold">Guarda estos códigos en un lugar seguro. Solo se muestran ahora y cada uno se usa una vez.</p><pre className="mt-3 whitespace-pre-wrap">{recovery.join("\n")}</pre></div>}
      {user.mfa_enabled && user.role === "candidate" && <form className="mt-4 flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { await api.post("/account/mfa/disable", { password: data.get("password"), code: data.get("code") }); setRecovery([]); await refreshUser(); setMessage("Autenticación desactivada"); }); }}><label className="text-sm">Contraseña<input className="field-control mt-1" name="password" type="password" required autoComplete="current-password" /></label><label className="text-sm">Código<input className="field-control mt-1" name="code" required autoComplete="one-time-code" /></label><button disabled={busy} className="button-secondary self-end">Desactivar</button></form>}
    </section>
    {user.role === "candidate" && <section id="security-privacy" className="surface-card security-section p-5"><h2 className="flex items-center gap-3 text-lg font-bold"><Eye size={21} className="text-[var(--accent)]" />Privacidad</h2>{privacy && <div className="mt-4 space-y-3">{Object.entries({ share_evidence: "Compartir evidencias con empresas de mis procesos", notify_new_skills: "Avisar a empresas de mis procesos cuando acredite habilidades", personalize_recommendations: "Usar mis decisiones explícitas de interés para personalizar recomendaciones y evaluar modelos" }).map(([key, label]) => <label className="privacy-choice" key={key}><input type="checkbox" checked={privacy[key]} onChange={(event) => setPrivacy({ ...privacy, [key]: event.target.checked })} />{label}</label>)}<p className="text-xs text-[var(--muted)]">Desactivar la personalización borra tus interacciones y los artefactos experimentales que pudieran incluirlas.</p><button disabled={busy} className="button-primary" onClick={async () => { if (!privacy.personalize_recommendations && !await confirm({ title: "Guardar privacidad", description: "Al desactivar la personalización se borran tus decisiones guardadas y los modelos experimentales que las incluyan.", confirmLabel: "Guardar preferencias" })) return; act(async () => { const { data } = await api.put("/account/privacy", privacy); setPrivacy(data); setMessage("Preferencias guardadas"); }); }}>Guardar preferencias</button></div>}</section>}
    <section id="security-sessions" className="surface-card security-section p-5"><h2 className="flex items-center gap-3 text-lg font-bold"><Monitor size={21} className="text-[var(--accent)]" />Sesiones y dispositivos</h2><div className="mt-3 divide-y divide-[var(--line)]">{sessions.map((session) => <div key={session.id} className="flex flex-wrap items-center justify-between gap-3 py-3"><div><p className="text-sm font-semibold">{session.current ? "Este dispositivo" : "Otro dispositivo"}{session.revoked ? " · Cerrada" : ""}</p><p className="max-w-xl break-all text-xs text-[var(--muted)]">{session.device || "Dispositivo sin identificar"}</p><p className="text-xs text-[var(--muted)]">Último uso: {new Date(session.last_seen_at + "Z").toLocaleString("es-CO")}</p></div>{!session.revoked && <button disabled={busy} className="button-secondary" onClick={async () => { if (!await confirm({ title: "Cerrar esta sesión", description: session.current ? "Saldrás de la cuenta en este dispositivo." : "Este dispositivo tendrá que iniciar sesión de nuevo.", confirmLabel: "Cerrar sesión" })) return; act(async () => { if (session.current) await logout(); else { await api.delete(`/account/sessions/${session.id}`); await load(); } }); }}>Cerrar sesión</button>}</div>)}</div></section>
    <Link className="button-secondary inline-flex" to={params.get("invitation") ? `/equipo/invitacion?token=${encodeURIComponent(params.get("invitation"))}` : user.role === "candidate" ? "/candidato" : user.role === "company" ? "/empresa/equipo" : "/admin"}>Continuar a mi espacio</Link>
  </div>;
}
