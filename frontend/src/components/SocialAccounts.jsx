import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";

const labels = { google: "Google", github: "GitHub", linkedin: "LinkedIn" };

export function SocialAccounts({ user, providers = [], onSessionsChanged, mfaReview = false }) {
  const [identities, setIdentities] = useState(null);
  const [selection, setSelection] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  async function load() {
    const { data } = await api.get("/account/social-identities");
    setIdentities(data);
  }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const credentials = { password: data.get("password"), code: data.get("code") || null };
    form.reset();
    setBusy(true); setError(""); setMessage("");
    try {
      if (selection.unlink) {
        const result = await api.delete(`/account/social-identities/${selection.provider}`, { data: credentials });
        setMessage(result.data.message); setSelection(null); await load(); await onSessionsChanged();
      } else {
        const { data: result } = await api.post(`/account/social-identities/${selection.provider}/link`, credentials);
        window.location.assign(result.url);
      }
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="surface-card space-y-4 p-5">
    <h2 className="font-bold">Cuentas conectadas</h2>
    <p className="text-sm text-[var(--muted)]">Añade Google, GitHub o LinkedIn como otro método de acceso a esta cuenta. Autoriza únicamente una cuenta social que controles. Tu perfil, correo y habilidades se conservan.</p>
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
    {message && <p role="status" className="text-sm">{message}</p>}
    {!identities && !error && <p className="text-sm">Consultando tus conexiones…</p>}
    {!identities && error && <button className="button-secondary" disabled={busy} onClick={() => load().then(() => setError("")).catch((failure) => setError(getApiErrorMessage(failure)))}>Reintentar</button>}
    {identities && Object.entries(labels).map(([provider, label]) => {
      const linked = identities.some((row) => row.provider === provider);
      const enabled = providers.some((row) => row.id === provider && row.enabled);
      return <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] pt-3" key={provider}>
        <div><h3 className="font-semibold">{label}</h3><p className="text-xs text-[var(--muted)]">{linked ? "Vinculada" : enabled ? "Sin vincular" : "Proveedor sin configurar"}</p></div>
        <button className="button-secondary" disabled={busy || (!linked && !enabled)} onClick={() => { setSelection({ provider, unlink: linked }); setError(""); setMessage(""); }}>{linked ? `Desvincular ${label}` : `Vincular ${label}`}</button>
      </div>;
    })}
    {selection && <form key={`${selection.provider}:${selection.unlink}`} onSubmit={submit} className="space-y-3 rounded-xl border border-[var(--line)] p-4">
      <h3 className="font-semibold">{selection.unlink ? "Desvincular" : "Vincular"} {labels[selection.provider]}</h3>
      <p className="text-sm text-[var(--muted)]">{selection.unlink ? "Confirma tu contraseña para conservar el acceso por correo. Cerraremos las demás sesiones y cancelaremos los accesos sociales pendientes." : "Confirma tu acceso a TalentSync. Después elegirás la cuenta en el proveedor; la autorización vence en diez minutos."}</p>
      <label className="block text-sm">Contraseña actual de TalentSync<input name="password" className="field-control mt-1" required type="password" autoComplete="current-password" maxLength={72} /></label>
      {user.mfa_enabled && !mfaReview && <label className="block text-sm">Código de autenticación o recuperación<input name="code" className="field-control mt-1" required minLength={6} maxLength={128} autoComplete="one-time-code" /></label>}
      <div className="flex flex-wrap gap-3"><button disabled={busy} className="button-primary">{busy ? "Validando…" : selection.unlink ? "Confirmar desvinculación" : "Continuar al proveedor"}</button><button type="button" className="button-secondary" disabled={busy} onClick={() => setSelection(null)}>Cancelar</button></div>
    </form>}
    <p className="text-xs text-[var(--muted)]">Si te registraste con una cuenta social y aún no tienes contraseña, define una mediante <Link className="text-[var(--accent)]" to="/recuperar-acceso">Recuperar acceso</Link>. {mfaReview ? "La verificación en dos pasos está pausada durante esta revisión local." : "Los proveedores vinculados siguen sujetos al MFA de TalentSync."}</p>
  </section>;
}
