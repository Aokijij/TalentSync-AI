import { useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

export function ReopenJobModal({ job, onClose, onReopened }) {
  const [mode, setMode] = useState("continue");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  async function reopen() {
    setSaving(true);
    setError("");
    try {
      const { data } = await api.post(`/jobs/${job.id}/reopen`, { mode });
      await onReopened(data, mode);
      onClose();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible reabrir la vacante"));
    } finally { setSaving(false); }
  }
  return (
    <div className="fixed inset-0 z-[75] grid place-items-center bg-slate-950/65 p-4 backdrop-blur-sm">
      <section role="dialog" aria-modal="true" aria-labelledby="reopen-title" className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl">
        <p className="section-kicker">Reabrir vacante</p><h2 id="reopen-title" className="mt-2 text-xl font-bold">¿Cómo quieres volver a contratar?</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">{job.title}</p>
        <fieldset className="mt-5 space-y-3" disabled={saving}><legend className="sr-only">Tipo de proceso</legend>
          {[ ["continue", "Continuar con los mismos candidatos", "La vacante vuelve a estar activa. Se conservan los candidatos, sus estados, notas y seguimientos. No se enviarán notificaciones por reabrirla."], ["new", "Crear una nueva vacante", "Se publica una copia activa, sin candidatos ni seguimientos. La anterior permanece cubierta con todo su historial. Los seguidores compatibles podrán recibir el aviso de la nueva vacante."] ].map(([value, title, description]) => <label key={value} className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 ${mode === value ? "border-[var(--accent)] bg-[var(--accent)]/10" : "border-[var(--line)]"}`}><input className="mt-1" type="radio" name="reopen-mode" value={value} checked={mode === value} onChange={() => setMode(value)} /><span><span className="block text-sm font-bold">{title}</span><span className="mt-1 block text-xs leading-5 text-[var(--muted)]">{description}</span></span></label>)}
        </fieldset>
        {error && <p role="alert" className="mt-4 rounded-lg border border-[var(--error)] p-3 text-sm text-[var(--error)]">{error}</p>}
        <div className="mt-5 flex flex-wrap justify-end gap-2"><button type="button" className="button-secondary" disabled={saving} onClick={onClose}>Cancelar</button><button type="button" className="button-primary" disabled={saving} onClick={reopen}>{saving ? "Procesando…" : mode === "continue" ? "Reactivar y conservar proceso" : "Publicar nueva vacante"}</button></div>
      </section>
    </div>
  );
}
