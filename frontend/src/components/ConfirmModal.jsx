import { AlertTriangle, Trash2, X } from "lucide-react";

export function ConfirmModal({
  open,
  title,
  description,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  destructive = false,
  loading = false,
  onConfirm,
  onClose,
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[70] grid place-items-center bg-slate-950/60 p-4 backdrop-blur-sm"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !loading) onClose();
      }}
    >
      <section
        className="w-full max-w-md rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-description"
      >
        <div className="flex items-start justify-between gap-4">
          <div
            className={`grid h-12 w-12 shrink-0 place-items-center rounded-full ${destructive ? "bg-[var(--error)]/10 text-[var(--error)]" : "bg-[var(--warning)]/10 text-[var(--warning)]"}`}
          >
            {destructive ? <Trash2 size={21} /> : <AlertTriangle size={21} />}
          </div>
          <button
            type="button"
            className="button-ghost !h-10 !w-10 !p-0"
            onClick={onClose}
            disabled={loading}
            aria-label="Cerrar"
          >
            <X size={18} />
          </button>
        </div>
        <h2
          id="confirm-title"
          className="mt-5 text-xl font-bold text-[var(--ink-strong)]"
        >
          {title}
        </h2>
        <p
          id="confirm-description"
          className="mt-2 text-sm leading-6 text-[var(--muted)]"
        >
          {description}
        </p>
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            className="button-secondary"
            onClick={onClose}
            disabled={loading}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={destructive ? "button-danger" : "button-primary"}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Procesando…" : confirmLabel}
          </button>
        </div>
      </section>
    </div>
  );
}
