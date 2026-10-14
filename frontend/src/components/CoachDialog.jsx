import { useEffect, useId, useRef } from "react";
import { X, Sparkles } from "lucide-react";
import "../styles/dialog.css";

export function CoachDialog({ open, onClose, children, title = "Ideas para mejorar tu hoja de vida", className = "" }) {
  const titleId = useId();
  const dialog = useRef(null);
  useEffect(() => {
    if (!open) { dialog.current?.close(); return; }
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    dialog.current.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      dialog.current?.close();
      document.body.style.overflow = overflow;
      previous?.focus?.();
    };
  }, [open]);
  return <dialog ref={dialog} className={`profile-coach-dialog ${className}`} aria-labelledby={titleId} onCancel={onClose} onClick={(event) => { if (event.target === dialog.current) { const bounds = dialog.current.getBoundingClientRect(); if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose(); } }}>
    <header><div><Sparkles size={22} /><h2 id={titleId}>{title}</h2></div><button type="button" className="button-secondary" autoFocus aria-label="Cerrar ventana" onClick={onClose}><X size={20} /></button></header>
    {children}
  </dialog>;
}
