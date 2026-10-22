import { useEffect, useRef, useState } from "react";
import { Save, Trash2, X } from "lucide-react";
import { DateTimePicker } from "./DateTimePicker.jsx";
import { ConfirmModal } from "./ConfirmModal.jsx";
import { interviewInputUtc, interviewInputValue } from "../utils/interviewAgenda.js";
import "../styles/recruiter-dialog.css";

export function RecruiterProcessDialog({ application, onClose, onDelete, onSave }) {
  const root = useRef(null);
  const [notes, setNotes] = useState(application.recruiter_notes || "");
  const [interviewAt, setInterviewAt] = useState(
    interviewInputValue(application.interview_at),
  );
  const [confirmDelete, setConfirmDelete] = useState(false);
  useEffect(() => {
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    root.current?.querySelector("button")?.focus();
    return () => { document.body.style.overflow = overflow; previous?.focus?.(); };
  }, []);
  const changes = {
    recruiter_notes: notes || null,
    interview_at: interviewInputUtc(interviewAt),
  };
  return (
    <>
      <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
        <section ref={root} role="dialog" aria-modal="true" aria-labelledby="recruiter-process-title" className="recruiter-process-dialog" onKeyDown={(event) => {
          if (event.defaultPrevented || confirmDelete) return;
          if (event.key === "Escape") { event.preventDefault(); onClose(); }
          if (event.key === "Tab") {
            const controls = [...root.current.querySelectorAll('button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href]')].filter((element) => element.offsetParent !== null);
            const first = controls[0], last = controls.at(-1);
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
          }
        }}>
          <div className="flex items-start justify-between">
            <div>
              <p className="section-kicker">Gestionar proceso</p>
              <h2 id="recruiter-process-title" className="mt-1 text-xl font-bold">
                {application.candidate_name}
              </h2>
            </div>
            <button
              type="button"
              className="button-secondary !h-10 !w-10 !p-0"
              onClick={onClose}
              aria-label="Cerrar"
            >
              <X size={18} />
            </button>
          </div>
          <div className="mt-5 grid gap-4">
            <label className="text-sm font-semibold text-[var(--muted)]">
              Notas internas
              <textarea
                className="field-control mt-1 min-h-28"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Observaciones para el equipo de selección..."
              />
            </label>
            <DateTimePicker label="Fecha y hora de entrevista · hora de Colombia" value={interviewAt} onChange={setInterviewAt} />
            {interviewAt && !changes.interview_at && <p role="alert" className="text-sm text-[var(--error)]">Completa una fecha y una hora válidas antes de guardar.</p>}
            <p className="text-xs text-[var(--muted)]">Aplica estos cambios con «Guardar y notificar» en el tablero.</p>
          </div>
          <div className="mt-6 flex flex-wrap justify-between gap-3 border-t border-[var(--line)] pt-5">
            <button
              type="button"
              className="button-ghost text-[var(--error)]"
              disabled={["rejected", "accepted", "hired"].includes(application.status)}
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 size={16} />
              Finalizar participación
            </button>
            <div className="flex gap-2">
              <button
                type="button"
                className="button-secondary"
                onClick={onClose}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="button-primary"
                disabled={!!interviewAt && !changes.interview_at}
                onClick={() => onSave(changes)}
              >
                <Save size={16} />
                Preparar cambios
              </button>
            </div>
          </div>
        </section>
      </div>
      <ConfirmModal
        open={confirmDelete}
        title="Finalizar participación"
        description={`Se comunicará a ${application.candidate_name} que su participación ha finalizado. La postulación y su historial se conservarán.`}
        confirmLabel="Finalizar y notificar"
        destructive
        onClose={() => setConfirmDelete(false)}
        onConfirm={onDelete}
      />
    </>
  );
}
