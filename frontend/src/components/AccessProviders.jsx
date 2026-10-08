import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

export function AccessProviders({ candidate = true, availableOnly = false }) {
  const { accessOptions } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function start(provider) {
    setBusy(true); setError("");
    try {
      const { data } = await api.post(`/auth/social/${provider}/start`);
      localStorage.setItem("talentsync_last_method", provider);
      window.location.assign(data.url);
    } catch (failure) { setError(getApiErrorMessage(failure)); setBusy(false); }
  }
  return <div className="mt-5 space-y-2">
    {candidate && accessOptions.providers?.filter((provider) => !availableOnly || provider.enabled).map((provider) => <button key={provider.id} type="button" disabled={!provider.enabled || busy} onClick={() => start(provider.id)} title={provider.reason} className={`button-secondary w-full ${provider.enabled ? "" : "opacity-60"}`}>
      Continuar con {({ google: "Google", github: "GitHub", linkedin: "LinkedIn" })[provider.id]}{!provider.enabled && " · No disponible"}
    </button>)}
    {candidate && accessOptions.providers?.length > 0 && <p className="text-xs text-[var(--muted)]">El acceso social crea una cuenta de candidato. Los botones se habilitan al configurar el proveedor.</p>}
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
    {accessOptions.local_mail && <Link className="block text-xs font-semibold text-[var(--accent)]" to="/desarrollo/correos">Abrir bandeja de correo local</Link>}
  </div>;
}
