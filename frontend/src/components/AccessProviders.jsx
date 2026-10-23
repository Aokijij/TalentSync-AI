import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";
import { ProviderIcon } from "./ProviderIcon.jsx";
import "../styles/social-access.css";

export function AccessProviders({ candidate = true, availableOnly = false, registering = false }) {
  const { accessOptions } = useAuth();
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState("");
  async function start(provider) {
    setBusy(provider); setError("");
    try {
      const { data } = await api.post(`/auth/social/${provider}/start`);
      try { localStorage.setItem("talentsync_last_method", provider); } catch { /* Private browsing can block storage. */ }
      window.location.assign(data.url);
    } catch (failure) { setError(getApiErrorMessage(failure)); setBusy(false); }
  }
  const providers = candidate ? accessOptions.providers?.filter((provider) => !availableOnly || provider.enabled) || [] : [];
  return <div className="access-provider-options">
    {providers.length > 0 && <><p className="access-provider-caption">{registering ? "Crea tu cuenta con" : "O continúa con"}</p><div className="access-provider-buttons" role="group" aria-label={registering ? "Registro con proveedor" : "Acceso con proveedor"}>
      {providers.map((provider) => <button key={provider.id} type="button" disabled={!provider.enabled || !!busy} onClick={() => start(provider.id)} title={!provider.enabled ? provider.reason : undefined} className="button-secondary access-provider-button">
        <ProviderIcon provider={provider.id} /><span>{busy === provider.id ? "Abriendo…" : "Continuar con"} {({ google: "Google", github: "GitHub", linkedin: "LinkedIn" })[provider.id]}</span>
      </button>)}
    </div><p className="access-provider-note">{registering ? "Usaremos tu nombre y correo verificado. Después completarás tu perfil." : "Si es tu primera vez, crearemos tu cuenta de candidato. Si ya tienes cuenta por correo, vincula el proveedor desde Seguridad."}</p>{registering && <div className="access-provider-divider"><span>O usa tu correo</span></div>}</>}
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
    {accessOptions.local_mail && <Link className="block text-xs font-semibold text-[var(--accent)]" to="/desarrollo/correos">Abrir bandeja de correo local</Link>}
  </div>;
}
