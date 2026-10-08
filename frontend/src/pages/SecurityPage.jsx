import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { PageHeader } from "../components/PageHeader.jsx";

export function SecurityPage() {
  const { user, refreshUser, accessOptions, logout } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [privacy, setPrivacy] = useState(null);
  const [setup, setSetup] = useState(null);
  const [recovery, setRecovery] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try { const [a, b] = await Promise.all([api.get("/account/sessions"), api.get("/account/privacy")]); setSessions(a.data); setPrivacy(b.data); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
  }
  useEffect(() => { load(); }, []);
  async function act(action) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <div className="space-y-5">
    <PageHeader kicker="Tu cuenta" title="Seguridad y privacidad" description="Controla el acceso, las sesiones y cómo se comparten tus evidencias." />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}
    {message && <p role="status" className="surface-card p-4">{message}</p>}
    {user.role !== "candidate" && !user.mfa_enabled && <p className="surface-card p-4">Para operar como empresa o administrador, configura primero una aplicación autenticadora.</p>}
    <section className="surface-card p-5"><h2 className="font-bold">Correo electrónico</h2><p className="mt-2">{user.email} · {user.email_verified ? "Confirmado" : "Pendiente de confirmar"}</p>
      {!user.email_verified && <button disabled={busy} className="button-secondary mt-3" onClick={() => act(async () => { const { data } = await api.post("/account/verify-email"); setMessage(data.message); })}>Enviar confirmación</button>}
      {accessOptions.local_mail && <Link className="ml-3 text-sm text-[var(--accent)]" to="/desarrollo/correos">Bandeja local</Link>}
      <form className="mt-4 grid gap-3 sm:grid-cols-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/change-email", { email: data.get("email"), password: data.get("password") }); setMessage(result.data.message); }); }}>
        <label className="text-sm">Nuevo correo<input className="field-control mt-1" name="email" required type="email" autoComplete="email" /></label>
        <label className="text-sm">Contraseña actual<input className="field-control mt-1" name="password" required type="password" autoComplete="current-password" /></label>
        <button disabled={busy} className="button-secondary self-end">Solicitar cambio</button>
      </form>
    </section>
    <section className="surface-card p-5"><h2 className="font-bold">Autenticación de dos factores</h2><p className="mt-2 text-sm text-[var(--muted)]">{user.mfa_enabled ? "Activada. Puedes usar tu aplicación o un código de recuperación al ingresar." : "Añade la clave a una aplicación autenticadora y confirma con su código de seis dígitos."}</p>
      {!user.mfa_enabled && !setup && <form className="mt-4 flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/mfa/setup", { password: data.get("password") }); setSetup(result.data); }); }}>
        <label className="text-sm">Contraseña actual<input className="field-control mt-1" required name="password" type="password" autoComplete="current-password" /></label><button disabled={busy} className="button-primary self-end">Configurar autenticador</button>
      </form>}
      {setup && !user.mfa_enabled && <div className="mt-4 space-y-3"><p className="text-sm">Clave para introducir manualmente (no la compartas):</p><code className="block break-all rounded-lg bg-[var(--surface-subtle)] p-3">{setup.secret}</code>
        <form className="flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { const result = await api.post("/account/mfa/confirm", { code: data.get("code") }); setRecovery(result.data.recovery_codes); setSetup(null); await refreshUser(); await load(); }); }}><label className="text-sm">Código del autenticador<input className="field-control mt-1" name="code" required pattern="[0-9]{6}" inputMode="numeric" autoComplete="one-time-code" /></label><button disabled={busy} className="button-primary self-end">Activar y obtener recuperación</button></form>
      </div>}
      {recovery.length > 0 && <div className="mt-4 rounded-lg border border-[var(--line)] p-4"><p className="font-semibold">Guarda estos códigos en un lugar seguro. Solo se muestran ahora y cada uno se usa una vez.</p><pre className="mt-3 whitespace-pre-wrap">{recovery.join("\n")}</pre></div>}
      {user.mfa_enabled && user.role === "candidate" && <form className="mt-4 flex flex-wrap gap-3" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); act(async () => { await api.post("/account/mfa/disable", { password: data.get("password"), code: data.get("code") }); setRecovery([]); await refreshUser(); setMessage("Autenticación desactivada"); }); }}><label className="text-sm">Contraseña<input className="field-control mt-1" name="password" type="password" required autoComplete="current-password" /></label><label className="text-sm">Código<input className="field-control mt-1" name="code" required autoComplete="one-time-code" /></label><button disabled={busy} className="button-secondary self-end">Desactivar</button></form>}
    </section>
    <section className="surface-card p-5"><h2 className="font-bold">Privacidad</h2>{privacy && <div className="mt-4 space-y-3">{Object.entries({ share_evidence: "Compartir evidencias con empresas de mis procesos", notify_new_skills: "Avisar a empresas de mis procesos cuando acredite habilidades", personalize_recommendations: "Usar mis interacciones para personalizar recomendaciones" }).map(([key, label]) => <label className="flex items-center gap-3 text-sm" key={key}><input type="checkbox" checked={privacy[key]} onChange={(event) => setPrivacy({ ...privacy, [key]: event.target.checked })} />{label}</label>)}<button disabled={busy} className="button-primary" onClick={() => act(async () => { const { data } = await api.put("/account/privacy", privacy); setPrivacy(data); setMessage("Preferencias guardadas"); })}>Guardar preferencias</button></div>}</section>
    <section className="surface-card p-5"><h2 className="font-bold">Sesiones y dispositivos</h2><div className="mt-3 divide-y divide-[var(--line)]">{sessions.map((session) => <div key={session.id} className="flex flex-wrap items-center justify-between gap-3 py-3"><div><p className="text-sm font-semibold">{session.current ? "Este dispositivo" : "Otro dispositivo"}{session.revoked ? " · Cerrada" : ""}</p><p className="max-w-xl break-all text-xs text-[var(--muted)]">{session.device || "Dispositivo sin identificar"}</p><p className="text-xs text-[var(--muted)]">Último uso: {new Date(session.last_seen_at + "Z").toLocaleString("es-CO")}</p></div>{!session.revoked && <button disabled={busy} className="button-secondary" onClick={() => act(async () => { if (session.current) await logout(); else { await api.delete(`/account/sessions/${session.id}`); await load(); } })}>Cerrar sesión</button>}</div>)}</div></section>
    <Link className="button-secondary inline-flex" to={user.role === "candidate" ? "/candidato" : user.role === "company" ? "/empresa" : "/admin"}>Continuar a mi espacio</Link>
  </div>;
}
