import { useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  BriefcaseBusiness,
  Edit3,
  GripVertical,
  MapPin,
  Plus,
  Save,
  Search,
  Settings2,
  Sparkles,
  Trash2,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import { ReopenJobModal } from "../components/ReopenJobModal.jsx";

const stageAccents = [
  "var(--accent)",
  "#8b5cf6",
  "var(--warning)",
  "#f97316",
  "var(--success)",
  "var(--error)",
  "#14b8a6",
  "#ec4899",
];

const defaultStages = [
  { id: "submitted", title: "Recibidas" },
  { id: "reviewing", title: "En revisión" },
  { id: "interview", title: "Entrevista" },
  { id: "hired", title: "Contratados" },
  { id: "rejected", title: "No seleccionados" },
];

function columnsFor(job) {
  const stages =
    job?.pipeline_stages?.length >= 2 ? job.pipeline_stages : defaultStages;
  return stages.map((stage, index) => ({
    ...stage,
    accent: stageAccents[index % stageAccents.length],
  }));
}

function applicationStage(item) {
  const stage = item.pipeline_stage || item.status;
  return (
    {
      seen: "submitted",
      shortlisted: "reviewing",
      technical_interview: "interview",
      psychometric_test: "interview",
      accepted: "hired",
    }[stage] || stage
  );
}

export function CompanyApplicationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState(searchParams.get("job") || "");
  const [applications, setApplications] = useState([]);
  const [scores, setScores] = useState({});
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [draggedId, setDraggedId] = useState(null);
  const [overColumn, setOverColumn] = useState(null);
  const [showJobPicker, setShowJobPicker] = useState(false);
  const [showStageEditor, setShowStageEditor] = useState(false);
  const [pendingChanges, setPendingChanges] = useState({});
  const [confirmCoverage, setConfirmCoverage] = useState(false);
  const [showReopen, setShowReopen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api
      .get("/companies/me")
      .then(async ({ data: company }) => {
        const { data: allJobs } = await api.get("/jobs", {
          params: { status: "" },
        });
        const ownJobs = allJobs.filter((job) => job.company_id === company.id);
        setJobs(ownJobs);
        const requested = searchParams.get("job");
        const initial =
          ownJobs.find((job) => String(job.id) === requested) || ownJobs[0];
        if (initial) setJobId(String(initial.id));
      })
      .catch((requestError) =>
        setError(
          getApiErrorMessage(
            requestError,
            "No fue posible cargar las vacantes",
          ),
        ),
      );
  }, []);

  const selectedJob = jobs.find((job) => String(job.id) === jobId);
  const columns = useMemo(() => columnsFor(selectedJob), [selectedJob]);

  async function loadApplications() {
    if (!jobId) return;
    try {
      const [applicationsResponse, candidatesResponse] = await Promise.all([
        api.get(`/applications/jobs/${jobId}`),
        api
          .get(`/recommendations/jobs/${jobId}/candidates`)
          .catch(() => ({ data: [] })),
      ]);
      const hasUnseen = applicationsResponse.data.some(
        (item) => item.status === "submitted",
      );
      setApplications(applicationsResponse.data);
      const focused = searchParams.get("focus");
      if (focused) {
        const focusedApplication = applicationsResponse.data.find(
          (item) => String(item.id) === focused,
        );
        if (focusedApplication) setSelected(focusedApplication);
      }
      if (hasUnseen)
        api
          .put(`/applications/jobs/${jobId}/mark-seen`)
          .then(() =>
            setApplications((current) =>
              current.map((item) =>
                item.status === "submitted"
                  ? { ...item, status: "seen" }
                  : item,
              ),
            ),
          )
          .catch(() => {});
      setScores(
        {
          ...Object.fromEntries(
            candidatesResponse.data.map((candidate) => [
              candidate.user_id,
              candidate.match_percentage,
            ]),
          ),
          ...Object.fromEntries(
            applicationsResponse.data
              .filter((application) => application.adjusted_match_percentage != null)
              .map((application) => [application.user_id, application.adjusted_match_percentage]),
          ),
        },
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible cargar las postulaciones",
        ),
      );
    }
  }

  useEffect(() => {
    loadApplications();
  }, [jobId]);

  function selectJob(job) {
    setJobId(String(job.id));
    setSearchParams({ job: String(job.id) });
    setShowJobPicker(false);
    setPendingChanges({});
    setMessage("");
  }

  function queueUpdate(applicationId, changes) {
    setApplications((current) =>
      current.map((item) =>
        item.id === applicationId ? { ...item, ...changes } : item,
      ),
    );
    setPendingChanges((current) => ({
      ...current,
      [applicationId]: { ...(current[applicationId] || {}), ...changes },
    }));
    setMessage("");
    return true;
  }

  async function savePendingChanges() {
    const entries = Object.entries(pendingChanges);
    if (!entries.length) return;
    setSaving(true);
    setError("");
    try {
      await Promise.all(
        entries.map(([applicationId, changes]) =>
          api.put(`/applications/${applicationId}/status`, changes),
        ),
      );
      setPendingChanges({});
      await loadApplications();
      setMessage(
        `${entries.length} cambio${entries.length === 1 ? "" : "s"} guardado${entries.length === 1 ? "" : "s"}. Las notificaciones ya fueron enviadas.`,
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible guardar todos los cambios",
        ),
      );
    } finally {
      setSaving(false);
    }
  }

  async function coverJob() {
    if (!selectedJob || Object.keys(pendingChanges).length) return;
    setSaving(true);
    setError("");
    try {
      const { data } = await api.patch(`/jobs/${selectedJob.id}`, {
        status: "filled",
      });
      setJobs((current) =>
        current.map((job) => (job.id === data.id ? data : job)),
      );
      await loadApplications();
      setMessage(
        "Vacante marcada como cubierta. Las postulaciones restantes fueron finalizadas y notificadas.",
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "No fue posible cubrir la vacante"),
      );
    } finally {
      setSaving(false);
      setConfirmCoverage(false);
    }
  }

  async function remove(applicationId) {
    try {
      await api.delete(`/applications/${applicationId}`);
      setApplications((current) =>
        current.filter((item) => item.id !== applicationId),
      );
      setSelected(null);
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible eliminar la postulación",
        ),
      );
    }
  }

  async function saveStages(stages) {
    try {
      const { data } = await api.patch(`/jobs/${jobId}`, {
        pipeline_stages: stages,
      });
      setJobs((current) =>
        current.map((job) => (job.id === data.id ? data : job)),
      );
      setShowStageEditor(false);
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "No fue posible guardar las etapas"),
      );
    }
  }

  const grouped = useMemo(
    () =>
      Object.fromEntries(
        columns.map((column) => [
          column.id,
          applications.filter((item) => applicationStage(item) === column.id),
        ]),
      ),
    [applications, columns],
  );

  function drop(columnId) {
    if (draggedId == null) return;
    const application = applications.find((item) => item.id === draggedId);
    if (application && applicationStage(application) !== columnId)
      queueUpdate(draggedId, { pipeline_stage: columnId });
    setDraggedId(null);
    setOverColumn(null);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Proceso de selección"
        title="Tablero de candidatos"
        description="Organiza cada vacante por etapas y revisa fácilmente el avance de cada persona."
      />
      {error ? (
        <p className="rounded-[var(--radius-lg)] border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-[var(--error)]">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="rounded-[var(--radius-lg)] border border-[var(--success)] bg-[var(--success)]/10 px-4 py-3 text-[var(--success)]">
          {message}
        </p>
      ) : null}

      <section className="surface-card flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
            <BriefcaseBusiness size={20} />
          </span>
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-wide text-[var(--muted)]">
              Vacante seleccionada
            </p>
            <h2 className="truncate font-bold text-[var(--ink-strong)]">
              {selectedJob?.title || "Selecciona una vacante"}
            </h2>
            <p className="mt-1 text-xs text-[var(--muted)]">
              {applications.length} postulante
              {applications.length === 1 ? "" : "s"} en este proceso
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.keys(pendingChanges).length ? (
            <button
              type="button"
              className="button-primary"
              disabled={saving}
              onClick={savePendingChanges}
            >
              <Save size={16} />
              {saving
                ? "Guardando…"
                : `Guardar y notificar (${Object.keys(pendingChanges).length})`}
            </button>
          ) : null}
          {selectedJob ? (
            <button
              type="button"
              className="button-secondary"
              disabled={
                saving ||
                Object.keys(pendingChanges).length > 0 ||
                (selectedJob.status !== "filled" && !applications.some((item) => applicationStage(item) === "hired"))
              }
              title={
                Object.keys(pendingChanges).length
                  ? "Guarda primero los movimientos pendientes"
                  : selectedJob.status === "filled" ? "Elige si deseas continuar el proceso o publicar una nueva vacante" : "Finaliza el proceso cuando ya estén todas las personas contratadas"
              }
              onClick={() => selectedJob.status === "filled" ? setShowReopen(true) : setConfirmCoverage(true)}
            >
              {selectedJob.status === "filled"
                ? "Reabrir vacante cubierta"
                : "Marcar como cubierta"}
            </button>
          ) : null}
          <button
            type="button"
            className="button-secondary"
            onClick={() => setShowJobPicker(true)}
          >
            <Search size={16} />
            Elegir vacante
          </button>
          {selectedJob ? (
            <button
              type="button"
              className="button-outline"
              onClick={() => setShowStageEditor(true)}
            >
              <Settings2 size={16} />
              Editar etapas
            </button>
          ) : null}
        </div>
      </section>

      {jobId ? (
        <section
          className="overflow-x-auto pb-3"
          aria-label="Tablero de candidatos por etapas"
        >
          <div
            className="grid gap-4"
            style={{
              gridTemplateColumns: `repeat(${columns.length}, minmax(260px, 1fr))`,
              minWidth: `${columns.length * 276}px`,
            }}
          >
            {columns.map((column) => (
              <div
                key={column.id}
                className={`min-h-[460px] rounded-[var(--radius-xl)] border bg-[var(--surface-subtle)] p-3 transition-colors ${overColumn === column.id ? "border-[var(--accent)] bg-[var(--surface-hover)]" : "border-[var(--line)]"}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setOverColumn(column.id);
                }}
                onDragLeave={() => setOverColumn(null)}
                onDrop={() => drop(column.id)}
              >
                <div className="mb-3 flex items-center justify-between gap-2 px-1">
                  <div className="flex items-center gap-2">
                    <i
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ background: column.accent }}
                    />
                    <h2 className="text-sm font-bold text-[var(--ink-strong)]">
                      {column.title}
                    </h2>
                  </div>
                  <span className="rounded-full bg-[var(--surface)] px-2 py-0.5 text-xs font-bold text-[var(--muted)]">
                    {grouped[column.id]?.length ?? 0}
                  </span>
                </div>
                <div className="space-y-3">
                  {(grouped[column.id] ?? []).map((item) => (
                    <CandidateCard
                      key={item.id}
                      item={item}
                      score={scores[item.user_id]}
                      columns={columns}
                      onDragStart={() => setDraggedId(item.id)}
                      onOpen={() => setSelected(item)}
                      onMove={(pipelineStage) =>
                        queueUpdate(item.id, { pipeline_stage: pipelineStage })
                      }
                    />
                  ))}
                </div>
                {!grouped[column.id]?.length ? (
                  <div className="grid min-h-28 place-items-center rounded-[var(--radius-lg)] border border-dashed border-[var(--line)] px-4 text-center text-xs text-[var(--muted)]">
                    Suelta aquí una tarjeta
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      ) : (
        <div className="surface-card py-14 text-center text-sm text-[var(--muted)]">
          Publica o selecciona una vacante para iniciar un proceso.
        </div>
      )}

      {showJobPicker ? (
        <JobPickerModal
          jobs={jobs}
          selectedId={jobId}
          onSelect={selectJob}
          onClose={() => setShowJobPicker(false)}
        />
      ) : null}
      {showStageEditor && selectedJob ? (
        <StageEditorModal
          stages={columns.map(({ id, title }) => ({ id, title }))}
          counts={Object.fromEntries(
            columns.map((column) => [
              column.id,
              grouped[column.id]?.length ?? 0,
            ]),
          )}
          onSave={saveStages}
          onClose={() => setShowStageEditor(false)}
        />
      ) : null}
      {selected ? (
        <RecruiterModal
          application={selected}
          onClose={() => setSelected(null)}
          onDelete={() => remove(selected.id)}
          onSave={(changes) => {
            queueUpdate(selected.id, changes);
            setSelected(null);
          }}
        />
      ) : null}
      <ConfirmModal
        open={confirmCoverage}
        title="Marcar la vacante como cubierta"
        description="Esta acción cierra el proceso. Las personas que no estén en Contratados pasarán a No seleccionados y recibirán la notificación correspondiente. Úsala solo cuando ya hayas completado todas las contrataciones necesarias."
        confirmLabel="Sí, cubrir vacante y notificar"
        onClose={() => setConfirmCoverage(false)}
        onConfirm={coverJob}
      />
      {showReopen && selectedJob && <ReopenJobModal job={selectedJob} onClose={() => setShowReopen(false)} onReopened={async (job, mode) => { setJobs((current) => mode === "continue" ? current.map((item) => item.id === job.id ? job : item) : [...current, job]); selectJob(job); setMessage(mode === "continue" ? "Vacante reactivada. Los candidatos y sus seguimientos se conservaron, sin notificar cambios." : "Nueva vacante activa, sin candidatos. El proceso anterior conserva su historial."); }} />}
    </div>
  );
}

function CandidateCard({ item, score, columns, onDragStart, onOpen, onMove }) {
  const selectedStage = applicationStage(item);
  return (
    <article
      draggable
      onDragStart={(event) => {
        event.dataTransfer.effectAllowed = "move";
        onDragStart();
      }}
      className="cursor-grab rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 shadow-sm active:cursor-grabbing"
    >
      <div className="flex items-start gap-2">
        <GripVertical
          size={17}
          className="mt-0.5 shrink-0 text-[var(--muted)]"
        />
        <div className="min-w-0 flex-1">
          <button type="button" className="truncate text-left font-bold text-[var(--ink-strong)] hover:text-[var(--accent)] hover:underline" onClick={onOpen}>
            {item.candidate_name || `Candidato #${item.user_id}`}
          </button>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Postulado {new Date(item.created_at).toLocaleDateString("es-CO")}
          </p>
        </div>
      </div>
      {score != null ? (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="flex items-center gap-1 text-[var(--muted)]">
              <Sparkles size={13} />
              {item.screening_adjustment ? "Compatibilidad ajustada" : "Compatibilidad"}
            </span>
            <span className="text-[var(--accent)]">{Math.round(score)}%</span>
          </div>
          {item.screening_adjustment ? <p className="mt-1 text-[10px] text-[var(--muted)]">Base {Math.round(item.base_match_percentage ?? score)}% · preguntas {item.screening_adjustment > 0 ? "+" : ""}{item.screening_adjustment} pts</p> : null}
          <div className="mt-1.5 h-1.5 rounded-full bg-[var(--line)]">
            <div
              className="h-full rounded-full bg-[var(--accent)]"
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
      ) : null}
      <div className="mt-4 flex items-center gap-2">
        <button
          type="button"
          className="button-secondary button-sm flex-1"
          onClick={onOpen}
        >
          <Edit3 size={14} />
          Editar proceso
        </button>
        <Link
          className="button-ghost button-sm !px-2"
          to={`/empresa/candidatos/${item.user_id}?job=${item.job_id}`}
          aria-label="Ver perfil"
        >
          <UserRound size={16} />
        </Link>
      </div>
      <label className="mt-3 block text-[10px] font-bold uppercase tracking-wide text-[var(--muted)]">
        Mover a
        <select
          className="field-control input-sm mt-1"
          value={selectedStage}
          onChange={(event) => onMove(event.target.value)}
        >
          {columns.map((column) => (
            <option key={column.id} value={column.id}>
              {column.title}
            </option>
          ))}
        </select>
      </label>
    </article>
  );
}

function JobPickerModal({ jobs, selectedId, onSelect, onClose }) {
  const [query, setQuery] = useState("");
  const visible = jobs.filter((job) =>
    `${job.title} ${job.location || ""} ${job.sector || ""}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/55 p-4 backdrop-blur-sm">
      <section className="max-h-[88vh] w-full max-w-6xl overflow-hidden rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] shadow-2xl">
        <header className="flex items-start justify-between gap-4 border-b border-[var(--line)] p-5">
          <div>
            <p className="section-kicker">Procesos de selección</p>
            <h2 className="mt-1 text-2xl font-bold">Elegir una vacante</h2>
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
                        {job.applications_count ?? 0}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-bold ${job.status === "active" ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--warning)]/10 text-[var(--warning)]"}`}
                      >
                        {job.status === "active" ? "Activa" : job.status === "filled" ? "Cubierta" : "Pausada"}
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

function StageEditorModal({ stages: initialStages, counts, onSave, onClose }) {
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
      if (target < 0 || target >= next.length) return current;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  const addStage = () =>
    setStages((current) =>
      current.length >= 12
        ? current
        : [...current, { id: `custom_${Date.now()}`, title: "Nueva etapa" }],
    );
  const removeStage = (index) =>
    setStages((current) =>
      current.length <= 2
        ? current
        : current.filter((_, position) => position !== index),
    );
  return (
    <>
      <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/55 p-4 backdrop-blur-sm">
        <section className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl">
          <div className="flex items-start justify-between">
            <div>
              <p className="section-kicker">Configuración del tablero</p>
              <h2 className="mt-1 text-2xl font-bold">Editar etapas</h2>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Crea, elimina, renombra y reorganiza las fases de esta vacante.
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
                      value={stage.title}
                      maxLength={60}
                      onChange={(event) =>
                        updateTitle(index, event.target.value)
                      }
                    />
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
                    disabled={index === 0}
                    onClick={() => move(index, -1)}
                    aria-label="Subir etapa"
                  >
                    <ArrowUp size={15} />
                  </button>
                  <button
                    type="button"
                    className="button-ghost button-sm !px-2"
                    disabled={index === stages.length - 1}
                    onClick={() => move(index, 1)}
                    aria-label="Bajar etapa"
                  >
                    <ArrowDown size={15} />
                  </button>
                  <button
                    type="button"
                    className="button-ghost button-sm !px-2 text-[var(--error)]"
                    disabled={occupied || stages.length <= 2}
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
            Entre 2 y 12 etapas por vacante.
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

function RecruiterModal({ application, onClose, onDelete, onSave }) {
  const [notes, setNotes] = useState(application.recruiter_notes || "");
  const [interviewAt, setInterviewAt] = useState(
    application.interview_at ? application.interview_at.slice(0, 16) : "",
  );
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [confirmSave, setConfirmSave] = useState(false);
  const changes = {
    recruiter_notes: notes || null,
    interview_at: interviewAt ? new Date(interviewAt).toISOString() : null,
  };
  return (
    <>
      <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
        <div className="w-full max-w-2xl rounded-[var(--radius-2xl)] bg-[var(--surface)] p-6 shadow-xl">
          <div className="flex items-start justify-between">
            <div>
              <p className="section-kicker">Editar postulación</p>
              <h2 className="mt-1 text-xl font-bold">
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
            {application.screening_answers?.length ? (
              <section className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
                <div className="flex items-center justify-between gap-3"><h3 className="font-bold">Respuestas de postulación</h3><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${application.screening_adjustment >= 0 ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--warning)]/10 text-[var(--warning)]"}`}>{application.screening_adjustment > 0 ? "+" : ""}{application.screening_adjustment} puntos</span></div>
                <dl className="mt-3 space-y-3">{application.screening_answers.map((item, index) => <div key={`${item.question_id}-${index}`}><dt className="text-xs font-bold text-[var(--muted)]">{item.question || `Pregunta ${index + 1}`}</dt><dd className="mt-1 text-sm text-[var(--ink-strong)]">{item.answer}</dd></div>)}</dl>
                {application.adjusted_match_percentage != null ? <p className="mt-4 border-t border-[var(--line)] pt-3 text-sm"><strong>Compatibilidad para tu empresa:</strong> {Math.round(application.adjusted_match_percentage)}% <span className="text-[var(--muted)]">(base {Math.round(application.base_match_percentage || 0)}%)</span></p> : null}
              </section>
            ) : null}
            <label className="text-sm font-semibold text-[var(--muted)]">
              Notas internas
              <textarea
                className="field-control mt-1 min-h-28"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Observaciones para el equipo de selección..."
              />
            </label>
            <label className="text-sm font-semibold text-[var(--muted)]">
              Fecha y hora de entrevista
              <input
                className="field-control mt-1"
                type="datetime-local"
                value={interviewAt}
                onChange={(event) => setInterviewAt(event.target.value)}
              />
            </label>
          </div>
          <div className="mt-6 flex flex-wrap justify-between gap-3 border-t border-[var(--line)] pt-5">
            <button
              type="button"
              className="button-ghost text-[var(--error)]"
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 size={16} />
              Eliminar
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
                onClick={() => setConfirmSave(true)}
              >
                <Save size={16} />
                Guardar edición
              </button>
            </div>
          </div>
        </div>
      </div>
      <ConfirmModal
        open={confirmSave}
        title="Guardar cambios de la postulación"
        description={`Se actualizarán las notas y la entrevista de ${application.candidate_name}.`}
        confirmLabel="Sí, guardar cambios"
        onClose={() => setConfirmSave(false)}
        onConfirm={() => onSave(changes)}
      />
      <ConfirmModal
        open={confirmDelete}
        title="Eliminar del proceso"
        description={`Se eliminará la postulación de ${application.candidate_name}. Esta acción no se puede deshacer.`}
        confirmLabel="Eliminar postulación"
        destructive
        onClose={() => setConfirmDelete(false)}
        onConfirm={onDelete}
      />
    </>
  );
}
