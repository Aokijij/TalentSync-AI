import { useState } from "react";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";

const modalities = { remote: "Remota", hybrid: "Híbrida", onsite: "Presencial" };
export function SearchPreferences({ data, onSaved, alignment }) {
  const [pending, setPending] = useState(null);
  const shown = pending || data;
  const [error, setError] = useState(""), [busy, setBusy] = useState(false);

  async function toggle(key, value) {
    setBusy(true); setError(""); setPending({ ...data, [key]: value });
    try { await api.put("/matching/preferences", { [key]: value }); await onSaved?.(); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); setPending(null); }
  }
  const rows = data ? [
    ["salary_required", "Salario mínimo", data.minimum_salary != null ? `$${Number(data.minimum_salary).toLocaleString("es-CO")} COP` : null],
    ["modality_required", "Modalidad", data.modalities?.map((value) => modalities[value] || value).join(", ")],
    ["location_required", "Ubicación", data.locations?.join(", ")],
  ] : [];
  const requiredCount = rows.filter(([key]) => shown?.[key]).length;
  return <section className="match-preferences preference-toolbar">
    <details className="profile-conditions-disclosure"><summary><SlidersHorizontal size={18} aria-hidden="true" /><span><strong>Condiciones de tu perfil</strong><small>Salario, modalidad y ubicación{data ? ` · ${requiredCount} imprescindible${requiredCount === 1 ? "" : "s"}` : ""}</small></span><ChevronDown size={18} className="profile-conditions-chevron" aria-hidden="true" /></summary><div className="profile-conditions-body"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs text-[var(--muted)]">Usamos las preferencias de tu perfil. Activa las que deben cumplirse.</p><Link className="text-xs font-semibold text-[var(--accent)]" to="/perfil#preferencias">Editar en mi perfil →</Link></div>
    {!data && !error && <p role="status" className="mt-3 text-sm text-[var(--muted)]">Cargando condiciones…</p>}
    <div className="mt-3 grid gap-3 sm:grid-cols-3">{rows.map(([key, label, value]) => {
      const check = alignment?.checks?.find((row) => row.label === label);
      return <div key={key} className="match-condition"><p className="text-xs text-[var(--muted)]">{label}</p><strong className="mt-1 block text-sm">{value || "Sin definir en el perfil"}</strong><p className="my-2 text-xs text-[var(--muted)]">{check ? check.matches === true ? "Esta vacante cumple" : check.matches === false ? "Esta vacante no cumple" : "Dato no publicado por la vacante" : label === "Ubicación" && value ? "Sin restricción para trabajo remoto" : value ? "Preferencia de tu perfil" : "Define esta condición en tu perfil"}</p><label className="inline-flex items-center gap-2 text-xs font-semibold"><input type="checkbox" checked={!!shown[key]} disabled={busy || !value} onChange={(event) => toggle(key, event.target.checked)} />{label} imprescindible</label></div>;
    })}</div></div></details>
    {error && <p role="alert" className="mt-3 text-sm text-[var(--error)]">{error}</p>}
  </section>;
}
