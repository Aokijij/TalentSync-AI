import { useState } from "react";
import { CheckCircle2, Clock3, RefreshCw, AlertTriangle } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import "../styles/external-vacancies.css";

export function ExternalVacancyStatus({ job, admin = false, onChecked, onBusyChange }) {
  const [result, setResult] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState("");
  if (job.source_kind !== "external") return null;
  const available = result ? result.available : job.external_available;
  const state = result?.state || job.external_check_state;
  const reasons = job.external_admission_reasons || [];
  const manual = (result?.verification_method || job.external_verification_method) === "manual";
  const label = job.moderation_status === "held" ? "Retirada por administración" : reasons.length ? "Fuera del filtro del catálogo" : available ? manual ? "Revisada por administración" : "Vigencia comprobada" : state === "closed" ? "Retirada o vencida" : state === "unavailable" ? "Fuente no disponible" : "Vigencia por confirmar";
  const Icon = available ? CheckCircle2 : state === "closed" ? AlertTriangle : Clock3;
  const date = manual ? result?.manual_verified_at || job.external_manual_verified_at : result?.checked_at || job.external_checked_at;
  async function check() {
    setBusy(true); onBusyChange?.(true); setError("");
    try { const { data } = await api.post(`/admin/jobs/${job.id}/availability/check`, {}, { __quiet: true }); setResult(data); await onChecked?.(data); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); onBusyChange?.(false); }
  }
  return <div className="external-vacancy-status" data-available={!!available}><span><Icon size={15} /><strong>{label}</strong></span>{date && <small>Consulta: {new Date(date.endsWith("Z") ? date : `${date}Z`).toLocaleString("es-CO")}</small>}{reasons.length > 0 && <p>{reasons.map((reason) => ({ publication_missing: "Falta la fecha original de publicación.", publication_too_old: "La publicación supera tres meses.", publication_in_future: "La fecha de publicación no es válida.", insufficient_skills: "Se necesitan al menos tres habilidades distintas.", responsibilities_unclear: "Faltan funciones claras.", requirements_unclear: "Faltan requisitos suficientes.", experience_unspecified: "No se identifica la experiencia mínima.", education_unspecified: "Falta aclarar la formación solicitada.", clarity_pending: "Pendiente de la revisión de claridad." }[reason])).filter(Boolean).join(" ")}</p>}{admin && <button type="button" className="button-secondary button-sm" disabled={busy} onClick={check}><RefreshCw size={14} />{busy ? "Consultando…" : "Comprobar fuente"}</button>}{error && <p role="alert">{error}</p>}{result?.reason && <p>{result.reason}</p>}</div>;
}
