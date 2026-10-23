import { useAuth } from "../hooks/useAuth.js";
import { useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";
import { ProviderIcon } from "./ProviderIcon.jsx";
import "../styles/social-access.css";

export function AccessProviders({ candidate = true, availableOnly = false, registering = false, onlyProvider }) {
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
  const providers = candidate ? accessOptions.providers?.filter((provider) => ["google", "github"].includes(provider.id) && (!onlyProvider || provider.id === onlyProvider) && (!availableOnly || provider.enabled)) || [] : [];
  if (!providers.length) return null;
  return <div className="access-provider-options">
    {providers.length > 0 && <><p className="access-provider-caption">{registering ? "Crea tu cuenta con" : "O continúa con"}</p><div className="access-provider-buttons" role="group" aria-label={registering ? "Registro con proveedor" : "Acceso con proveedor"}>
      {providers.map((provider) => <button key={provider.id} type="button" aria-label={`Continuar con ${provider.id === "google" ? "Google" : "GitHub"}`} disabled={!provider.enabled || !!busy} onClick={() => start(provider.id)} title={!provider.enabled ? provider.reason : undefined} className="button-secondary access-provider-button">
        <ProviderIcon provider={provider.id} /><span>{busy === provider.id ? "Abriendo…" : provider.id === "google" ? "Google" : "GitHub"}</span>
      </button>)}
    </div>{registering && <><p className="access-provider-note">Usaremos tu nombre y correo verificado para crear tu perfil.</p><div className="access-provider-divider"><span>O usa tu correo</span></div></>}</>}
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
  </div>;
}
