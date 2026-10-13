import { SecuritySessions } from "../components/SecuritySessions.jsx";
import { ShieldCheck, Mail, LockKeyhole, Monitor, Eye } from "lucide-react";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { QRCodeSVG } from "qrcode.react";
import { useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { SocialAccounts } from "../components/SocialAccounts.jsx";

export function SecurityPage() {
  const [params] = useSearchParams();
  const location = useLocation();
  const requested = location.hash.replace("#security-", "");
  const { confirm } = useFeedback();
  const { user, refreshUser, accessOptions, logout } = useAuth();
  const panel = ["email", "mfa", "sessions", ...(user.role === "candidate" ? ["privacy"] : [])].includes(requested) ? requested : "email";
  const sections = [["email", "Correo y acceso", "Tu dirección y cuentas conectadas", Mail], ["mfa", "Verificación en dos pasos", "Estado del autenticador", ShieldCheck], ...(user.role === "candidate" ? [["privacy", "Privacidad", "Controla tus preferencias", Eye]] : []), ["sessions", "Dispositivos", "Dónde está abierta tu cuenta", Monitor]];
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
    <div className="security-status-bar"><span><Mail size={17} />{user.email_verified ? "Correo confirmado" : "Correo por confirmar"}</span><span><ShieldCheck size={17} />{accessOptions.mfa_review ? "Verificación en pausa local" : user.mfa_enabled ? "Verificación activa" : "Autenticador sin configurar"}</span><span><Monitor size={17} />{sessions.filter((row) => !row.revoked).length} sesiones activas</span></div>
    <div className="security-workspace"><nav className="security-section-nav" aria-label="Secciones de seguridad">{sections.map(([id, label, detail, Icon]) => <Link key={id} aria-current={panel === id ? "page" : undefined} to={{ pathname: location.pathname, search: location.search, hash: `#security-${id}` }}><Icon size={20} /><span><strong>{label}</strong><small>{detail}</small></span></Link>)}</nav><div className="security-content">
    {panel === "mfa" && user.role === "company" && !accessOptions.mfa_review && accessOptions.company_mfa_required === false && !user.mfa_enabled && <div className="learning-published"><ShieldCheck /><p>El autenticador es opcional para empresas en este entorno de revisión. Puedes configurarlo cuando quieras.</p></div>}
    {panel === "mfa" && user.role === "admin" && !accessOptions.mfa_review && accessOptions.admin_mfa_required === false && <div className="learning-published"><ShieldCheck /><p>Revisión local: acceso administrativo sin segundo factor. Tu configuración del autenticador se conserva.</p></div>}

    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}
    {message && <p role="status" className="surface-card p-4">{message}</p>}
    {!accessOptions.mfa_review && (user.role === "admin" && accessOptions.admin_mfa_required !== false || user.role === "company" && accessOptions.company_mfa_required !== false) && !user.mfa_enabled && <p className="surface-card p-4">Para operar como empresa o administrador, configura primero una aplicación autenticadora.</p>}
    {panel === "email" && <><section id="security-email" className="security-panel"><h2 className="flex items-center gap-3 text-lg font-bold"><Mail size={21} className="text-[var(--accent)]" />Correo electrónico</h2><p className="mt-2">{user.email} · {user.email_verified ? "Confirmado" : "Pendiente de confirmar"}</p>
      {!user.email_verified && <button disabled={busy} className="button-secondary mt-3" onClick={() => act(async () => { const { data } = await api.post("/account/verify-email"); setMessage(data.message); })}>Enviar confirmación</button>}
      {accessOptions.local_mail && <Link className="ml-3 text-sm text-[var(--accent)]" to="/desarrollo/correos">Bandeja local</Link>}
      <form className="security-email-form" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/change-email", { email: data.get("email"), password: data.get("password") }); setMessage(result.data.message); }); }}>
        <label className="text-sm">Nuevo correo<input className="field-control mt-1" name="email" required type="email" autoComplete="off" /></label>
        <label className="text-sm">Contraseña actual<input className="field-control mt-1" name="password" required type="password" autoComplete="current-password" /></label>
        <footer><p>Confirma el cambio con tu contraseña actual.</p><button disabled={busy} className="button-primary">Solicitar cambio</button></footer>
      </form>
    </section>
    {user.role === "candidate" && accessOptions.mode === "session" && <SocialAccounts user={user} providers={accessOptions.providers} onSessionsChanged={load} mfaReview={accessOptions.mfa_review} />}
    </>}
    {panel === "mfa" && (accessOptions.mfa_review ? <section id="security-mfa" className="security-panel"><h2 className="font-bold">Verificación en dos pasos pausada</h2><p className="mt-2 text-sm text-[var(--muted)]">Durante la revisión local, todos los roles pueden entrar con su contraseña sin código adicional. Tu autenticador y códigos de recuperación se conservan para reactivarlos después.</p></section> : <section id="security-mfa" className="security-panel"><h2 className="flex items-center gap-3 text-lg font-bold"><LockKeyhole size={21} className="text-[var(--accent)]" />Autenticación de dos factores</h2><p className="mt-2 text-sm text-[var(--muted)]">{user.mfa_enabled ? "Activada. Puedes usar tu aplicación o un código de recuperación al ingresar." : "Añade la clave a una aplicación autenticadora y confirma con su código de seis dígitos."}</p>
      {!user.mfa_enabled && !setup && <form className="mt-4 flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/mfa/setup", { password: data.get("password") }); setSetup(result.data); }); }}>
        <label className="text-sm">Contraseña actual<input className="field-control mt-1" required name="password" type="password" autoComplete="current-password" /></label><button disabled={busy} className="button-primary self-end">Configurar autenticador</button>
      </form>}
      {setup && !user.mfa_enabled && <div className="mt-4 space-y-3"><ol className="list-inside list-decimal space-y-2 text-sm"><li>Abre tu aplicación autenticadora y elige añadir una cuenta.</li><li>Escanea este QR con la aplicación.</li><li>Escribe aquí el código de seis dígitos que muestra la aplicación.</li></ol><div className="inline-block rounded-xl bg-white p-4"><QRCodeSVG value={setup.uri} size={192} level="M" title="QR para configurar tu autenticador" /></div><details><summary className="cursor-pointer text-sm">¿No puedes escanear? Introducir clave manual</summary><code className="mt-2 block break-all rounded-lg bg-[var(--surface-subtle)] p-3">{setup.secret}</code></details>
        <form className="flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/mfa/confirm", { code: data.get("code") }); setRecovery(result.data.recovery_codes); setSetup(null); await refreshUser(); await load(); }); }}><label className="text-sm">Código del autenticador<input className="field-control mt-1" name="code" required pattern="[0-9]{6}" maxLength={6} placeholder="123456" title="Introduce los seis números de tu aplicación, no la clave de configuración" inputMode="numeric" autoComplete="one-time-code" /></label><button disabled={busy} className="button-primary self-end">Activar y obtener recuperación</button></form>
      </div>}
      {recovery.length > 0 && <div className="mt-4 rounded-lg border border-[var(--line)] p-4"><p className="font-semibold">Guarda estos códigos en un lugar seguro. Solo se muestran ahora y cada uno se usa una vez.</p><pre className="mt-3 whitespace-pre-wrap">{recovery.join("\n")}</pre></div>}
      {user.mfa_enabled && user.role === "candidate" && <form className="mt-4 flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { await api.post("/account/mfa/disable", { password: data.get("password"), code: data.get("code") }); setRecovery([]); await refreshUser(); setMessage("Autenticación desactivada"); }); }}><label className="text-sm">Contraseña<input className="field-control mt-1" name="password" type="password" required autoComplete="current-password" /></label><label className="text-sm">Código<input className="field-control mt-1" name="code" required autoComplete="one-time-code" /></label><button disabled={busy} className="button-secondary self-end">Desactivar</button></form>}
    </section>)}
    {panel === "privacy" && user.role === "candidate" && <section id="security-privacy" className="security-panel"><h2 className="flex items-center gap-3 text-lg font-bold"><Eye size={21} className="text-[var(--accent)]" />Privacidad</h2>{privacy && <div className="mt-4 space-y-3">{Object.entries({ share_evidence: "Compartir evidencias con empresas de mis procesos", notify_new_skills: "Avisar a empresas de mis procesos cuando acredite habilidades", personalize_recommendations: "Usar mis decisiones explícitas de interés para personalizar recomendaciones y evaluar modelos" }).map(([key, label]) => <label className="privacy-choice" key={key}><input type="checkbox" checked={privacy[key]} onChange={(event) => setPrivacy({ ...privacy, [key]: event.target.checked })} />{label}</label>)}<p className="text-xs text-[var(--muted)]">Desactivar la personalización borra tus interacciones y los artefactos experimentales que pudieran incluirlas.</p><button disabled={busy} className="button-primary" onClick={async () => { if (!privacy.personalize_recommendations && !await confirm({ title: "Guardar privacidad", description: "Al desactivar la personalización se borran tus decisiones guardadas y los modelos experimentales que las incluyan.", confirmLabel: "Guardar preferencias" })) return; act(async () => { const { data } = await api.put("/account/privacy", privacy); setPrivacy(data); setMessage("Preferencias guardadas"); }); }}>Guardar preferencias</button></div>}</section>}
    {panel === "sessions" && <SecuritySessions sessions={sessions} busy={busy} onRevoke={async (session) => { if (!await confirm({ title: "Cerrar esta sesión", description: session.current ? "Saldrás de la cuenta en este dispositivo." : "Este dispositivo tendrá que iniciar sesión de nuevo.", confirmLabel: "Cerrar sesión" })) return; act(async () => { if (session.current) await logout(); else { await api.delete(`/account/sessions/${session.id}`); await load(); } }); }} />}
    </div></div>
    <Link className="button-secondary inline-flex" to={params.get("invitation") ? `/equipo/invitacion?token=${encodeURIComponent(params.get("invitation"))}` : user.role === "candidate" ? "/candidato" : user.role === "company" ? "/empresa/equipo" : "/admin"}>Continuar a mi espacio</Link>
  </div>;
}
