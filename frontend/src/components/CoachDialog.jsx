import { useEffect, useRef } from "react";
import { X, Sparkles } from "lucide-react";

export function CoachDialog({ open, onClose, children }) {
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
  return <dialog ref={dialog} className="profile-coach-dialog" aria-labelledby="profile-coach-title" onCancel={onClose} onClick={(event) => { if (event.target === dialog.current) { const bounds = dialog.current.getBoundingClientRect(); if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose(); } }}>
    <header><div><Sparkles size={22} /><h2 id="profile-coach-title">Ideas para mejorar tu hoja de vida</h2></div><button type="button" className="button-secondary" autoFocus aria-label="Cerrar ayuda" onClick={onClose}><X size={20} /></button></header>
    {children}
  </dialog>;
}
