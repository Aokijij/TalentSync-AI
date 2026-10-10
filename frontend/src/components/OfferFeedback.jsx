import { useEffect, useState } from "react";
import { MessageSquare } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

const REASONS = { salary: "Salario", requirements: "Requisitos", unclear: "Falta de claridad", modality: "Modalidad o ubicación", process: "Proceso de selección", other: "Otro motivo" };

export function OfferFeedback({ jobId }) {
  const [reason, setReason] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setReason(null); setError("");
    api.get(`/hiring/feedback/${jobId}`).then(({ data }) => { if (active) setReason(data.reason); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [jobId]);
  async function submit(value) {
    setBusy(true); setError("");
    try {
      if (value) await api.put(`/hiring/feedback/${jobId}`, { reason: value });
      else await api.delete(`/hiring/feedback/${jobId}`);
      setReason(value);
    } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <details className="surface-card offer-opinion"><summary><MessageSquare size={18} />¿Esta oferta no encaja contigo?</summary><p className="mt-3 text-sm text-[var(--muted)]">Puedes indicar el motivo de forma voluntaria. La empresa verá resultados agrupados desde cinco respuestas, sin tu nombre. Esta opinión no cambia tu compatibilidad ni activa la personalización.</p><div className="offer-opinion-options">{Object.entries(REASONS).map(([key, label]) => <button type="button" disabled={busy} aria-pressed={reason === key} key={key} onClick={() => submit(key)}>{label}</button>)}</div>{reason && <p role="status" className="mt-3 text-sm">Opinión guardada. <button type="button" className="offer-text-button" disabled={busy} onClick={() => submit(null)}>Retirar mi opinión</button></p>}{error && <p role="alert" className="mt-3 text-sm text-[var(--error)]">{error}</p>}</details>;
}
