import { useState } from "react";
import { ArrowDown, ArrowUp, MapPin, Plus, Save, Search, Trash2, UsersRound, X } from "lucide-react";
import { ConfirmModal } from "../ConfirmModal.jsx";
export function JobPickerModal({ jobs, selectedId, onSelect, onClose }) {
  const [query, setQuery] = useState("");
  const visible = jobs.filter((job) =>
    `${job.title} ${job.location || ""} ${job.sector || ""}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/55 p-4 backdrop-blur-xs">
      <section role="dialog" aria-modal="true" aria-labelledby="board-job-picker-title" className="max-h-[88vh] w-full max-w-6xl overflow-hidden rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] shadow-2xl">
        <header className="flex items-start justify-between gap-4 border-b border-[var(--line)] p-5">
          <div>
            <p className="section-kicker">Procesos de selección</p>
            <h2 id="board-job-picker-title" className="mt-1 text-2xl font-bold">Elegir una vacante</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Consulta la información y cuántos candidatos tiene cada proceso.
            </p>
          </div>
          <button
            type="button"
            className="button-secondary !h-10 !w-10 !p-0"
            onClick={onClose}
            aria-label="Cerrar"
          >
            <X size={18} />
          </button>
        </header>
        <div className="p-5">
          <label className="relative block">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
              size={17}
            />
            <input
              className="field-control !pl-10"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por cargo, ciudad o sector"
            />
          </label>
          <div className="mt-4 max-h-[56vh] overflow-auto rounded-[var(--radius-lg)] border border-[var(--line)]">
            <table className="w-full min-w-[880px] text-left text-sm">
              <thead className="sticky top-0 bg-[var(--surface-subtle)] text-xs uppercase tracking-wide text-[var(--muted)]">
                <tr>
                  <th className="px-4 py-3">Vacante</th>
                  <th className="px-4 py-3">Ubicación</th>
                  <th className="px-4 py-3">Sector</th>
                  <th className="px-4 py-3">Candidatos</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3 text-right">Selección</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((job) => (
                  <tr
                    key={job.id}
                    className="border-t border-[var(--line)] hover:bg-[var(--surface-hover)]"
                  >
                    <td className="px-4 py-4">
                      <p className="font-bold text-[var(--ink-strong)]">
                        {job.title}
                      </p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {job.skills?.slice(0, 3).join(" · ") ||
                          "Sin habilidades detectadas"}
                      </p>
                    </td>
                    <td className="px-4 py-4 text-[var(--muted)]">
                      <span className="inline-flex items-center gap-1">
                        <MapPin size={14} />
                        {job.location || "Flexible"}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-[var(--muted)]">
                      {job.sector || "Sin sector"}
                    </td>
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center gap-1.5 font-bold text-[var(--ink-strong)]">
                        <UsersRound size={15} />
                        {job.applications_count ?? "—"}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-bold ${job.status === "active" ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--warning)]/10 text-[var(--warning)]"}`}
                      >
                        {({ active: "Activa", filled: "Cubierta", paused: "Pausada", draft: "Borrador", closed: "Cerrada" })[job.status] || job.status}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <button
                        type="button"
                        className={
                          String(job.id) === selectedId
                            ? "button-outline button-sm"
                            : "button-primary button-sm"
                        }
                        onClick={() => onSelect(job)}
                      >
                        {String(job.id) === selectedId
                          ? "Seleccionada"
                          : "Seleccionar"}
                      </button>
                    </td>
                  </tr>
                ))}
                {!visible.length ? (
                  <tr>
                    <td
                      colSpan="6"
                      className="px-5 py-12 text-center text-[var(--muted)]"
                    >
                      No hay vacantes que coincidan con la búsqueda.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

export function StageEditorModal({ stages: initialStages, counts, onSave, onClose }) {
  const [stages, setStages] = useState(initialStages);
  const [confirmSave, setConfirmSave] = useState(false);
  const updateTitle = (index, title) =>
    setStages((current) =>
      current.map((stage, position) =>
        position === index ? { ...stage, title } : stage,
      ),
    );
  const move = (index, offset) =>
    setStages((current) => {
      const next = [...current];
      const target = index + offset;
      if (index === 0 || target <= 0 || target >= next.length) return current;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  const addStage = () =>
    setStages((current) =>
      current.length >= 12
        ? current
        : [...current.filter((stage) => !["hired", "rejected"].includes(stage.id)), { id: `custom_${Date.now()}`, title: "Nueva etapa" }, ...current.filter((stage) => ["hired", "rejected"].includes(stage.id))],
    );
  const removeStage = (index) =>
    setStages((current) =>
      current.length <= 2
        ? current
        : current.filter((_, position) => position !== index),
    );
  return (
    <>
      <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/55 p-4 backdrop-blur-xs">
        <section role="dialog" aria-modal="true" aria-label="Editar etapas" className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl">
          <div className="flex items-start justify-between">
            <div>
              <p className="section-kicker">Configuración del tablero</p>
              <h2 className="mt-1 text-2xl font-bold">Editar etapas</h2>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Organiza las etapas activas. La bandeja de entrada y los resultados finales conservan su función.
              </p>
            </div>
            <button
              type="button"
              className="button-secondary !h-10 !w-10 !p-0"
              onClick={onClose}
            >
              <X size={18} />
            </button>
          </div>
          <div className="mt-5 space-y-3">
            {stages.map((stage, index) => {
              const occupied = (counts[stage.id] ?? 0) > 0;
              return (
                <div
                  key={stage.id}
                  className="flex items-center gap-2 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-3"
                >
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--accent)]/10 text-xs font-bold text-[var(--accent)]">
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <input
                      className="field-control input-sm"
                      aria-label={`Nombre de etapa ${index + 1}`}
                      value={stage.title}
                      maxLength={60}
                      onChange={(event) =>
                        updateTitle(index, event.target.value)
                      }
                    />
                    <p className="mt-1 text-[11px] text-[var(--accent)]">{({ submitted: "Entrada · Bandeja de revisión", reviewing: "Revisión de evidencias", interview: "Entrevistas · Programadas y pendientes de respuesta", hired: "Cierre · Contratación", rejected: "Cierre · No seleccionado" })[stage.id] || "Etapa activa personalizada"}</p>
                    {occupied ? (
                      <p className="mt-1 text-[11px] text-[var(--muted)]">
                        {counts[stage.id]} candidato(s): muévelos antes de
                        eliminar esta etapa.
                      </p>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    className="button-ghost button-sm !px-2"
                    disabled={index <= 1}
                    onClick={() => move(index, -1)}
                    aria-label="Subir etapa"
                  >
                    <ArrowUp size={15} />
                  </button>
                  <button
                    type="button"
                    className="button-ghost button-sm !px-2"
                    disabled={index === 0 || index === stages.length - 1}
                    onClick={() => move(index, 1)}
                    aria-label="Bajar etapa"
                  >
                    <ArrowDown size={15} />
                  </button>
                  <button
                    type="button"
                    className="button-ghost button-sm !px-2 text-[var(--error)]"
                    disabled={index === 0 || occupied || stages.length <= 2}
                    onClick={() => removeStage(index)}
                    aria-label={`Eliminar ${stage.title}`}
                    title={
                      occupied
                        ? "Mueve primero los candidatos de esta etapa"
                        : "Eliminar etapa"
                    }
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              );
            })}
          </div>
          <button
            type="button"
            className="button-outline mt-4"
            disabled={stages.length >= 12}
            onClick={addStage}
          >
            <Plus size={16} />
            Agregar etapa
          </button>
          <p className="mt-2 text-xs text-[var(--muted)]">
            Entre 2 y 12 etapas. La entrada permanece primero y los cierres conservan su función.
          </p>
          <footer className="mt-6 flex justify-end gap-2 border-t border-[var(--line)] pt-5">
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
              disabled={stages.some((stage) => stage.title.trim().length < 2)}
              onClick={() => setConfirmSave(true)}
            >
              <Save size={16} />
              Guardar etapas
            </button>
          </footer>
        </section>
      </div>
      <ConfirmModal
        open={confirmSave}
        title="Actualizar las etapas"
        description="Se guardarán la estructura, los nombres y el orden del tablero únicamente para esta vacante. Los candidatos conservarán su fase actual."
        confirmLabel="Sí, actualizar etapas"
        onClose={() => setConfirmSave(false)}
        onConfirm={() =>
          onSave(
            stages.map((stage) => ({ ...stage, title: stage.title.trim() })),
          )
        }
      />
    </>
  );
}
