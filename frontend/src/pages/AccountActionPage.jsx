import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";

export function AccountActionPage({ recover = false }) {
  const [params] = useSearchParams();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { refreshUser, accessOptions } = useAuth();
  const purpose = params.get("purpose");
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    const data = new FormData(event.currentTarget);
    try {
      const response = recover
        ? await api.post("/auth/password/request", { email: data.get("email") })
        : await api.post("/auth/action/confirm", { purpose, token: params.get("token"), password: purpose === "reset" ? data.get("password") : null });
      setMessage(response.data.message);
      if (purpose === "verify") await refreshUser().catch(() => {});
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <main className="grid min-h-screen place-items-center bg-[var(--canvas)] p-5"><section className="surface-card w-full max-w-lg p-7">
    <p className="section-kicker">TalentSync · Tu cuenta</p>
    <h1 className="mt-3 text-2xl font-bold">{recover ? "Recuperar acceso" : purpose === "reset" ? "Define tu nueva contraseña" : "Confirmar cambio"}</h1>
    <p className="mt-3 text-sm text-[var(--muted)]">{recover ? "Te enviaremos instrucciones si existe una cuenta con ese correo." : "Confirma la acción solicitada. El enlace solo se puede utilizar una vez."}</p>
    {message ? <p role="status" className="mt-5">{message}</p> : <form className="mt-5 space-y-4" onSubmit={submit}>
      {recover && <label className="block">Correo<input required name="email" type="email" autoComplete="email" className="field-control mt-2" /></label>}
      {!recover && purpose === "reset" && <label className="block">Nueva contraseña<input required name="password" type="password" minLength={12} maxLength={72} autoComplete="new-password" className="field-control mt-2" /><span className="text-xs text-[var(--muted)]">Al menos 12 caracteres. Se cerrarán las sesiones existentes.</span></label>}
      {error && <p role="alert" className="text-[var(--error)]">{error}</p>}
      <button disabled={busy} className="button-primary" type="submit">{busy ? "Procesando…" : recover ? "Enviar instrucciones" : "Confirmar"}</button>
    </form>}
    <div className="mt-5 flex flex-wrap gap-4 text-sm text-[var(--accent)]"><Link to="/login">Volver al acceso</Link>{accessOptions.local_mail && <Link to="/desarrollo/correos">Bandeja local</Link>}</div>
  </section></main>;
}
