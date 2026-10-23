import { useEffect, useRef, useState } from "react";
import { CalendarClock, Save, Trash2, X } from "lucide-react";
import { getApiErrorMessage } from "../api/client.js";
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
  const [mode, setMode] = useState(application.interview_details?.mode || "virtual");
  const [location, setLocation] = useState(application.interview_details?.location || "");
  const [minutes, setMinutes] = useState(application.interview_details?.minutes || 45);
  const [instructions, setInstructions] = useState(application.interview_details?.instructions || "");
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const closed = !!application.released_at || ["rejected", "accepted", "hired"].includes(application.status);
  const [confirmDelete, setConfirmDelete] = useState(false);
  useEffect(() => {
    const previous = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    root.current?.querySelector("button")?.focus();
    return () => { document.body.style.overflow = overflow; previous?.focus?.(); };
  }, []);
  const changes = {
    ...(Object.hasOwn(application, "recruiter_notes") ? { recruiter_notes: notes || null } : {}),
    ...(!closed ? { interview_at: interviewInputUtc(interviewAt), interview_details: interviewAt ? { mode, location: location.trim(), minutes: Number(minutes), instructions: instructions.trim() } : null } : {}),
  };
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    if (!closed && interviewAt && (!changes.interview_at || (interviewAt !== interviewInputValue(application.interview_at) && new Date(changes.interview_at) <= new Date()))) { setError("Elige una fecha y hora futuras para la entrevista."); return; }
    setBusy(true); setError("");
    try { await onSave(changes); }
    catch (failure) { setError(getApiErrorMessage(failure, "No pudimos guardar. Tus datos siguen aquí; revisa e inténtalo de nuevo.")); }
    finally { setBusy(false); }
  }
  async function finalize() {
    if (busy) return;
    setBusy(true); setError("");
    try { await onDelete(); }
    catch (failure) { setError(getApiErrorMessage(failure)); setConfirmDelete(false); }
    finally { setBusy(false); }
  }
  return (
    <>
      <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
        <section ref={root} role="dialog" aria-modal="true" aria-label={application.candidate_name || "Gestionar proceso"} className="recruiter-process-dialog" onKeyDown={(event) => {
          if (event.defaultPrevented || confirmDelete || busy) return;
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
              <h2 className="mt-1 text-xl font-bold">
                {application.candidate_name}
              </h2>
            </div>
            <button
              type="button"
              className="button-secondary !h-10 !w-10 !p-0"
              disabled={busy}
              onClick={onClose}
              aria-label="Cerrar"
            >
              <X size={18} />
            </button>
          </div>
          <form onSubmit={submit} className="recruiter-schedule-form">
            <div className="recruiter-dialog-fields">
            {error && <p role="alert" className="schedule-error">{error}</p>}
            <fieldset disabled={busy || closed} className="schedule-fields">
              <legend><CalendarClock size={18} />{application.interview_at ? "Gestionar entrevista" : "Programar entrevista"}</legend>
              <DateTimePicker label="Fecha y hora · Colombia (UTC−5)" value={interviewAt} onChange={setInterviewAt} />
              {interviewAt && <>
                <div className="schedule-grid">
                  <label>Modalidad<select className="field-control" value={mode} onChange={(e) => { setMode(e.target.value); setLocation(""); }}><option value="virtual">Virtual</option><option value="in_person">Presencial</option></select></label>
                  <label>Duración<select className="field-control" value={minutes} onChange={(e) => setMinutes(e.target.value)}>{[15,30,45,60,90,120,180].map((value) => <option key={value} value={value}>{value} minutos</option>)}</select></label>
                </div>
                <label>{mode === "virtual" ? "Enlace de la videollamada" : "Dirección de la entrevista"}<input className="field-control" type={mode === "virtual" ? "url" : "text"} pattern={mode === "virtual" ? "https://.*" : undefined} required minLength={3} maxLength={1000} value={location} onChange={(e) => setLocation(e.target.value)} placeholder={mode === "virtual" ? "https://meet.google.com/…" : "Ciudad, dirección, edificio y oficina"} /></label>
                <label>Indicaciones para el candidato (opcional)<textarea className="field-control" rows={2} maxLength={2000} value={instructions} onChange={(e) => setInstructions(e.target.value)} placeholder="Qué debe preparar, persona de contacto o acceso al edificio" /></label>
              </>}
              {application.interview_at && interviewAt && <button type="button" className="button-ghost schedule-cancel" onClick={() => setInterviewAt("")}>Cancelar esta entrevista</button>}
              {application.interview_at && !interviewAt && <p className="schedule-warning">Al guardar se cancelará la entrevista y se avisará al candidato.</p>}
            </fieldset>
            {Object.hasOwn(application, "recruiter_notes") && <details className="schedule-notes"><summary>Notas internas del proceso</summary><label>Notas internas<textarea className="field-control" value={notes} disabled={busy} onChange={(e) => setNotes(e.target.value)} placeholder="Solo visibles para el equipo de selección" /></label></details>}
            <p className="schedule-save-note">La entrevista se guarda al confirmar. El candidato recibe una notificación y el cambio queda en el historial.</p>
            </div>
          <div className="recruiter-dialog-actions">
            <button
              type="button"
              className="button-ghost text-[var(--error)]"
              disabled={busy || closed}
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 size={16} />
              Finalizar participación
            </button>
            <div className="flex gap-2">
              <button
                type="button"
                className="button-secondary"
                disabled={busy}
                onClick={onClose}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="button-primary"
                disabled={busy || (!closed && !!interviewAt && !changes.interview_at)}
              >
                <Save size={16} />
                {busy ? "Guardando…" : "Guardar y notificar"}
              </button>
            </div>
          </div>
          </form>
        </section>
      </div>
      <ConfirmModal
        open={confirmDelete}
        title="Finalizar participación"
        description={`Se comunicará a ${application.candidate_name} que su participación ha finalizado. La postulación y su historial se conservarán.`}
        confirmLabel="Finalizar y notificar"
        destructive
        onClose={() => { if (!busy) setConfirmDelete(false); }}
        loading={busy}
        onConfirm={finalize}
      />
    </>
  );
}
