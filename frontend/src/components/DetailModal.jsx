import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { ListChecks, X } from "lucide-react";

export function DetailModal({ title, description, onClose, children }) {
  const root = useRef(null), id = useId();
  useEffect(() => {
    const previous = document.activeElement, overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    root.current?.focus();
    const keyboard = (event) => {
      if (event.key === "Escape") { event.preventDefault(); onClose(); }
      if (event.key === "Tab") {
        const controls = [...root.current.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), summary, [tabindex="0"]')].filter((element) => element.getClientRects().length);
        const first = controls[0], last = controls.at(-1);
        if (event.shiftKey && (document.activeElement === first || document.activeElement === root.current)) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && (document.activeElement === last || document.activeElement === root.current)) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener("keydown", keyboard);
    return () => { document.removeEventListener("keydown", keyboard); document.body.style.overflow = overflow; previous?.focus(); };
  }, [onClose]);
  return createPortal(<div className="detail-modal-overlay" onClick={(event) => event.stopPropagation()} onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section className="detail-modal" ref={root} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby={id} aria-describedby={description ? `${id}-description` : undefined}><header><span className="detail-modal-icon"><ListChecks size={24} /></span><div><p className="section-kicker">TU COMPATIBILIDAD</p><h2 id={id}>{title}</h2>{description && <p id={`${id}-description`} className="detail-modal-description">{description}</p>}</div><button type="button" className="detail-modal-close" aria-label="Cerrar detalle" onClick={onClose}><X size={20} /></button></header><div className="detail-modal-content">{children}</div><footer><span>Información declarada · No es una acreditación</span><button type="button" className="button-secondary button-sm" onClick={onClose}>Listo</button></footer></section></div>, document.body);
}
