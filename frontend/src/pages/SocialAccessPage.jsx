import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";

export function SocialAccessPage() {
  const [params] = useSearchParams();
  const status = params.get("status");
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await api.post("/auth/social/complete", { code: new FormData(event.currentTarget).get("code") }, { __skipSessionEvent: true });
      await refreshUser(); navigate("/candidato", { replace: true });
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  const message = status === "existing"
    ? "El correo o la cuenta social ya pertenecen a una cuenta existente. Usa su método original de acceso. Para añadir un proveedor a tu cuenta, ingresa y abre Seguridad. Las cuentas no se unen automáticamente."
    : status === "unavailable" ? "Este proveedor aún no está configurado. Puedes ingresar con correo."
      : "El acceso no se completó: pudo cancelarse, vencer o iniciarse en otro navegador. Vuelve a intentarlo desde el login.";
  return <main className="grid min-h-screen place-items-center bg-[var(--canvas)] p-5">
    <section className="surface-card w-full max-w-md space-y-5 p-7">
      <h1 className="text-2xl font-bold">{status === "mfa" ? "Confirma tu segundo factor" : "Acceso social"}</h1>
      {status === "mfa" ? <form onSubmit={submit} className="space-y-4">
        <p className="text-sm text-[var(--muted)]">Ya validamos tu cuenta social. Completa la autenticación de TalentSync en los próximos cinco minutos.</p>
        <label className="block text-sm font-semibold">Código de autenticación o recuperación<input className="field-control mt-2" name="code" required maxLength={40} autoComplete="one-time-code" autoFocus /></label>
        <button className="button-primary w-full" disabled={busy}>{busy ? "Validando…" : "Completar acceso"}</button>
      </form> : <p className="text-sm text-[var(--muted)]">{message}</p>}
      {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
      <Link className="button-secondary w-full" to="/login">Volver al inicio de sesión</Link>
    </section>
  </main>;
}
