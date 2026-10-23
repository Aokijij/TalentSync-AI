import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { ShieldCheck } from "lucide-react";
import { AccessProviders } from "../components/AccessProviders.jsx";
import { socialFailure } from "../utils/socialAccess.js";

export function SocialAccessPage({ administrative = false }) {
  const [params] = useSearchParams();
  const status = params.get("status");
  const provider = ["google", "github"].includes(params.get("provider")) ? params.get("provider") : undefined;
  const failure = socialFailure(status, params.get("reason"), provider);
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await api.post(administrative ? "/auth/admin-sso/complete" : "/auth/social/complete", { code: new FormData(event.currentTarget).get("code") }, { __skipSessionEvent: true });
      await refreshUser(); navigate(administrative ? "/admin" : "/candidato", { replace: true });
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  const message = administrative ? "El acceso corporativo no se completó. Revisa que la cuenta pertenezca al dominio configurado y tenga acceso administrativo aprovisionado; después vuelve a iniciar el flujo."
    : failure.message;
  return <main className="grid min-h-screen place-items-center bg-[var(--canvas)] p-5">
    <section className="surface-card social-access-result w-full max-w-md space-y-5 p-7">
      <div className="social-access-result-icon"><ShieldCheck size={25} aria-hidden="true" /></div>
      {failure.provider && <p className="social-access-result-provider">Acceso con {failure.provider}</p>}
      <h1 className="text-2xl font-bold">{status === "mfa" ? "Confirma tu segundo factor" : administrative ? "Acceso corporativo" : failure.title}</h1>
      {status === "mfa" ? <form onSubmit={submit} className="space-y-4">
        <p className="text-sm text-[var(--muted)]">Ya validamos tu cuenta {administrative ? "corporativa" : "social"}. Completa la autenticación de TalentSync en los próximos cinco minutos.</p>
        <label className="block text-sm font-semibold">Código de autenticación o recuperación<input className="field-control mt-2" name="code" required maxLength={40} autoComplete="one-time-code" autoFocus /></label>
        <button className="button-primary w-full" disabled={busy}>{busy ? "Validando…" : "Completar acceso"}</button>
      </form> : <p className="text-sm text-[var(--muted)]">{message}</p>}
      {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
      {!administrative && status !== "mfa" && failure.retry && <AccessProviders availableOnly onlyProvider={provider} />}
      <Link className="button-secondary w-full" to={administrative ? "/acceso-administracion" : "/login"}>{administrative || status === "mfa" ? "Volver al inicio de sesión" : "Entrar con mi correo"}</Link>
      {!administrative && failure.reference && <p className="social-access-reference">Referencia: {failure.reference}</p>}
    </section>
  </main>;
}
