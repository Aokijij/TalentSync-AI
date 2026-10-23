import { useEffect, useRef, useId, useState } from "react";
import { AlertTriangle, Info, Trash2, X } from "lucide-react";
import "../styles/feedback.css";
import { getApiErrorMessage } from "../api/client.js";

export function ConfirmModal({ open, title, description, details = [], confirmLabel = "Confirmar", cancelLabel = "Cancelar", destructive = false, tone = destructive ? "danger" : "info", loading = false, className = "", onConfirm, onClose }) {
  const root = useRef(null), cancel = useRef(null), id = useId();
  const inFlight = useRef(false);
  const [pending, setPending] = useState(false), [error, setError] = useState("");
  const busy = loading || pending;
  useEffect(() => {
    if (!open) return;
    setPending(false); setError("");
    const previous = document.activeElement, overflow = document.body.style.overflow;
    const node = root.current;
    node.showModal();
    document.body.style.overflow = "hidden";
    cancel.current?.focus();
    return () => { node.close(); document.body.style.overflow = overflow; if (previous?.isConnected) previous.focus(); };
  }, [open]);
  async function submit() {
    if (loading || inFlight.current) return;
    inFlight.current = true; setPending(true); setError("");
    try { await onConfirm(); }
    catch (failure) { if (root.current?.open) setError(getApiErrorMessage(failure, "No se pudo completar la acción. Vuelve a intentarlo.")); }
    finally { inFlight.current = false; if (root.current?.open) setPending(false); }
  }
  if (!open) return null;
  const Icon = tone === "danger" ? Trash2 : tone === "warning" ? AlertTriangle : Info;
  return <dialog className={`confirmation-dialog ${className}`} data-tone={tone} ref={root} role="alertdialog" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`}
    aria-busy={busy} onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }}>
    <div className="confirmation-heading"><span className="confirmation-icon"><Icon size={21} /></span><button type="button" className="button-ghost !h-9 !w-9 !p-0" aria-label="Cerrar confirmación" disabled={busy} onClick={onClose}><X size={18} /></button></div>
    <h2 id={`${id}-title`}>{title}</h2><p className="confirmation-description" id={`${id}-description`}>{description}</p>
    {details.length > 0 && <ul className="confirmation-details">{details.map((detail) => <li key={detail}>{detail}</li>)}</ul>}
    {error && <p className="confirmation-error" role="alert">{error}</p>}
    <footer className="confirmation-actions"><button ref={cancel} type="button" className="button-secondary" disabled={busy} onClick={onClose}>{cancelLabel}</button><button type="button" className={destructive ? "button-danger" : "button-primary"} disabled={busy} onClick={submit}>{busy ? "Procesando…" : confirmLabel}</button></footer>
  </dialog>;
}
