import { useEffect, useRef, useId } from "react";
import { AlertTriangle, Info, Trash2, X } from "lucide-react";
import "../styles/feedback.css";

export function ConfirmModal({ open, title, description, details = [], confirmLabel = "Confirmar", cancelLabel = "Cancelar", destructive = false, tone = destructive ? "danger" : "info", loading = false, className = "", onConfirm, onClose }) {
  const root = useRef(null), cancel = useRef(null), id = useId();
  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement, overflow = document.body.style.overflow;
    const node = root.current;
    node.showModal();
    document.body.style.overflow = "hidden";
    cancel.current?.focus();
    return () => { node.close(); document.body.style.overflow = overflow; if (previous?.isConnected) previous.focus(); };
  }, [open]);
  if (!open) return null;
  const Icon = tone === "danger" ? Trash2 : tone === "warning" ? AlertTriangle : Info;
  return <dialog className={`confirmation-dialog ${className}`} data-tone={tone} ref={root} role="alertdialog" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`}
    onCancel={(event) => { event.preventDefault(); if (!loading) onClose(); }}>
    <div className="confirmation-heading"><span className="confirmation-icon"><Icon size={21} /></span><button type="button" className="button-ghost !h-9 !w-9 !p-0" aria-label="Cerrar confirmación" disabled={loading} onClick={onClose}><X size={18} /></button></div>
    <h2 id={`${id}-title`}>{title}</h2><p className="confirmation-description" id={`${id}-description`}>{description}</p>
    {details.length > 0 && <ul className="confirmation-details">{details.map((detail) => <li key={detail}>{detail}</li>)}</ul>}
    <footer className="confirmation-actions"><button ref={cancel} type="button" className="button-secondary" disabled={loading} onClick={onClose}>{cancelLabel}</button><button type="button" className={destructive ? "button-danger" : "button-primary"} disabled={loading} onClick={onConfirm}>{loading ? "Procesando…" : confirmLabel}</button></footer>
  </dialog>;
}
