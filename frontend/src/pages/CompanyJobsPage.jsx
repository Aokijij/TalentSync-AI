import { useEffect, useMemo, useRef, useState } from "react";
import {
  BriefcaseBusiness,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Edit3,
  Eye,
  MapPin,
  PauseCircle,
  PlayCircle,
  Plus,
  Search,
  Trash2,
  UsersRound,
  X,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import {
  COLOMBIA_LOCATIONS,
  COLOMBIAN_DEPARTMENTS,
  departmentForCity,
} from "../constants/colombianCities.js";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";
import { ReopenJobModal } from "../components/ReopenJobModal.jsx";
import { languageLevelLabel } from "../constants/languages.js";

const NEW_JOB_DEFAULTS = {
  title: "",
  description: "",
  requirements: "",
  salary: "",
  location: "",
  department: "",
  modality: "remote",
  employment_type: "full_time",
  sector: JOB_SECTORS[0],
  benefits: "",
  languages: [],
  application_questions: [],
};

export function CompanyJobsPage() {
  const { register, handleSubmit, reset, watch, setValue } = useForm({
    defaultValues: NEW_JOB_DEFAULTS,
  });
  const preview = watch();
  const selectedDepartment = watch("department");
  const [jobs, setJobs] = useState([]);
  const [company, setCompany] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [pendingSave, setPendingSave] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [reopeningJob, setReopeningJob] = useState(null);
  const [publishedJob, setPublishedJob] = useState(null);
  const formErrorRef = useRef(null);

  useEffect(() => {
    if (showModal && error) formErrorRef.current?.scrollIntoView({ block: "center" });
  }, [showModal, error]);

  async function load() {
    const [companyResponse, jobsResponse] = await Promise.all([
      api.get("/companies/me"),
      api.get("/jobs", { params: { status: "" } }),
    ]);
    setCompany(companyResponse.data);
    setJobs(
      jobsResponse.data.filter(
        (job) => job.company_id === companyResponse.data.id,
      ),
    );
  }

  useEffect(() => {
    load().catch((requestError) =>
      setError(
        getApiErrorMessage(requestError, "No fue posible cargar tus vacantes"),
      ),
    );
  }, []);

  const availableSectors = useMemo(
    () =>
      JOB_SECTORS.filter((sector) => jobs.some((job) => job.sector === sector)),
    [jobs],
  );
  const filteredJobs = useMemo(
    () =>
      jobs.filter((job) => {
        const matchesQuery =
          `${job.title} ${job.description} ${job.location || ""} ${job.department || ""} ${job.skills?.join(" ") || ""}`
            .toLowerCase()
            .includes(query.trim().toLowerCase());
        return (
          matchesQuery &&
          (statusFilter === "all" || job.status === statusFilter) &&
          (sectorFilter === "all" || job.sector === sectorFilter)
        );
      }),
    [jobs, query, statusFilter, sectorFilter],
  );
  const pageSize = 6;
  const pageCount = Math.max(1, Math.ceil(filteredJobs.length / pageSize));
  const safePage = Math.min(page, pageCount);
  const visibleJobs = filteredJobs.slice((safePage - 1) * pageSize, safePage * pageSize);

  useEffect(() => setPage(1), [query, statusFilter, sectorFilter]);

  function formPayload(values) {
    return {
      ...values,
      sector: values.sector || JOB_SECTORS[0],
      salary: values.salary ? Number(values.salary) : null,
      benefits:
        typeof values.benefits === "string"
          ? values.benefits
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean)
          : (values.benefits ?? []),
    };
  }

  function submitJob(values) {
    if (values.languages?.some((item) => item.name.trim().length < 2)) {
      setError("Idiomas: escribe el nombre de cada idioma o elimina la fila vacía.");
      return;
    }
    const invalidQuestion = (values.application_questions || []).find(
      (question) => {
        const normalizedOptions = (question.options || []).map((option) => option.trim());
        return (
          question.prompt.trim().length < 5 ||
          (question.type === "choice" &&
            (normalizedOptions.length < 2 ||
              normalizedOptions.some((option) => !option) ||
              new Set(normalizedOptions).size !== normalizedOptions.length))
        );
      },
    );
    if (invalidQuestion) {
      setError("Preguntas de postulación: escribe una pregunta clara y, cuando corresponda, al menos dos opciones diferentes y completas.");
      return;
    }
    setError("");
    const payload = formPayload(values);
    setPendingSave(payload);
  }

  async function persistJob(payload) {
    setError("");
    setMessage("");
    setSaving(true);
    try {
      if (editingJob) {
        await api.patch(`/jobs/${editingJob.id}`, payload);
        setMessage("Vacante actualizada correctamente.");
      } else {
        const { data } = await api.post("/jobs", payload);
        setPublishedJob(data);
        setMessage("Vacante publicada y comparada con los perfiles disponibles.");
      }
      closeForm();
      await load();
    } catch (requestError) {
      setPendingSave(null);
      setError(
        getApiErrorMessage(requestError, "No fue posible guardar la vacante"),
      );
    } finally {
      setSaving(false);
    }
  }

  function openCreate() {
    setError("");
    setEditingJob(null);
    setPendingSave(null);
    setShowPreview(false);
    reset(NEW_JOB_DEFAULTS);
    setShowModal(true);
  }

  async function editJob(job) {
    setError("");
    setEditingJob(job);
    setPendingSave(null);
    setShowPreview(false);
    let questions = [];
    try {
      const response = await api.get(`/jobs/${job.id}/application-questions`);
      questions = response.data;
    } catch {
      questions = [];
    }
    reset({
      ...job,
      department: job.department || departmentForCity(job.location),
      benefits: (job.benefits || []).join(", "),
      application_questions: questions,
    });
    setShowModal(true);
  }

  function closeForm() {
    setShowModal(false);
    setShowPreview(false);
    setEditingJob(null);
    setPendingSave(null);
    reset(NEW_JOB_DEFAULTS);
  }

  async function toggle(job) {
    if (job.status === "filled") { setReopeningJob(job); return; }
    try {
      await api.patch(`/jobs/${job.id}`, {
        status: job.status === "active" ? "paused" : "active",
      });
      await load();
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible cambiar el estado de la vacante",
        ),
      );
    }
  }

  async function removeJob(job) {
    setDeleting(true);
    try {
      await api.delete(`/jobs/${job.id}`);
      setMessage("Vacante eliminada correctamente.");
      setPendingDelete(null);
      await load();
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "No fue posible eliminar la vacante"),
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Gestión de vacantes"
        title={`Oportunidades de ${company?.name ?? "tu empresa"}`}
        description="Publica, pausa y conecta cada vacante con el talento compatible."
        actions={
          <button type="button" onClick={openCreate} className="button-primary">
            <Plus size={16} />
            Publicar vacante
          </button>
        }
      />
      {message || error ? (
        <p
          className={`rounded-[var(--radius-lg)] border px-4 py-3 text-sm ${error ? "border-[var(--error)] bg-[var(--error)]/10 text-[var(--error)]" : "border-[var(--success)] bg-[var(--success)]/10 text-[var(--success)]"}`}
        >
          {error || message}
        </p>
      ) : null}

      <section>
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <p className="section-kicker">Tus oportunidades</p>
            <h2 className="mt-1 text-xl font-bold">Vacantes publicadas</h2>
          </div>
          <span className="text-sm font-semibold text-[var(--muted)]">
            {jobs.length} en total
          </span>
        </div>
        <div className="surface-card mb-5 grid gap-3 p-4 md:grid-cols-[1fr_190px_240px]">
          <label className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
              size={17}
            />
            <input
              className="field-control !pl-10"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por cargo, ciudad o habilidad"
            />
          </label>
          <select
            className="field-control"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">Todos los estados</option>
            <option value="active">Activas</option>
            <option value="paused">Pausadas</option>
            <option value="filled">Cubiertas</option>
          </select>
          <select
            className="field-control"
            value={sectorFilter}
            onChange={(event) => setSectorFilter(event.target.value)}
          >
            <option value="all">Sectores publicados</option>
            {availableSectors.map((sector) => (
              <option key={sector} value={sector}>
                {sector}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {visibleJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onEdit={() => editJob(job)}
              onToggle={() => toggle(job)}
              onDelete={() => setPendingDelete(job)}
            />
          ))}
          {!filteredJobs.length ? (
            <div className="surface-card col-span-full py-14 text-center">
              <BriefcaseBusiness className="mx-auto text-[var(--muted)]" />
              <p className="mt-3 text-sm text-[var(--muted)]">
                {jobs.length
                  ? "No hay vacantes que coincidan con los filtros."
                  : "Aún no has publicado vacantes."}
              </p>
            </div>
          ) : null}
        </div>
        {filteredJobs.length > pageSize ? <nav className="surface-card mt-4 flex items-center justify-between p-4" aria-label="Paginación de vacantes publicadas"><p className="text-sm text-[var(--muted)]">Mostrando {(safePage - 1) * pageSize + 1}–{Math.min(safePage * pageSize, filteredJobs.length)} de {filteredJobs.length}</p><div className="flex items-center gap-2"><button type="button" className="button-secondary button-sm" disabled={safePage === 1} onClick={() => setPage((current) => current - 1)}><ChevronLeft size={15} />Anterior</button><span className="px-2 text-sm font-bold">{safePage} / {pageCount}</span><button type="button" className="button-secondary button-sm" disabled={safePage === pageCount} onClick={() => setPage((current) => current + 1)}>Siguiente<ChevronRight size={15} /></button></div></nav> : null}
      </section>

      {showModal ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/55 p-4 backdrop-blur-sm">
          <section className="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl sm:p-7">
            <header className="flex items-start justify-between gap-4 border-b border-[var(--line)] pb-5">
              <div>
                <p className="section-kicker">
                  {editingJob ? "Editar oportunidad" : "Nueva oportunidad"}
                </p>
                <h2 className="mt-1 text-2xl font-bold">
                  {editingJob ? "Editar vacante" : "Publicar vacante"}
                </h2>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  Completa la información; podrás revisar la vista del candidato
                  en un modal independiente.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="button-outline"
                  onClick={() => setShowPreview(true)}
                >
                  <Eye size={16} />
                  Vista del candidato
                </button>
                <button
                  type="button"
                  className="button-secondary !h-10 !w-10 !p-0"
                  onClick={closeForm}
                >
                  <X size={18} />
                </button>
              </div>
            </header>
            <form
              id="job-form"
              className="mt-6 space-y-5"
              onSubmit={handleSubmit(submitJob, (errors) => setError(Object.values(errors).map((item) => item.message).join(". ") || "Completa los campos obligatorios."))}
            >
              {error && <p ref={formErrorRef} role="alert" tabIndex={-1} className="sticky top-0 z-10 rounded-xl border border-[var(--error)] bg-[var(--surface)] p-4 text-sm text-[var(--error)]"><strong>No se guardó la vacante.</strong> {error}</p>}
              <Field label="Cargo">
                <input
                  className="field-control"
                  placeholder="Ej. Analista financiero"
                  {...register("title", { required: "Cargo: completa este campo", minLength: { value: 2, message: "Cargo: escribe al menos 2 caracteres" }, maxLength: { value: 180, message: "Cargo: usa como máximo 180 caracteres" }, setValueAs: (value) => value.trim() })}
                />
              </Field>
              <div className="grid gap-5 md:grid-cols-2">
                <Field label="Descripción">
                  <textarea
                    className="field-control min-h-52 resize-y"
                    placeholder="Responsabilidades, equipo e impacto del cargo"
                    {...register("description", { required: "Descripción: completa este campo", minLength: { value: 10, message: "Descripción: escribe al menos 10 caracteres" }, setValueAs: (value) => value.trim() })}
                  />
                </Field>
                <Field label="Requisitos y habilidades">
                  <textarea
                    className="field-control min-h-52 resize-y"
                    placeholder="Formación, experiencia y conocimientos requeridos"
                    {...register("requirements", { required: "Requisitos: completa este campo", minLength: { value: 10, message: "Requisitos: escribe al menos 10 caracteres" }, setValueAs: (value) => value.trim() })}
                  />
                </Field>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <Field label="Salario">
                  <input
                    className="field-control"
                    type="number"
                    placeholder="COP"
                    {...register("salary")}
                  />
                </Field>
                <Field label="Departamento">
                  <select
                    className="field-control"
                    {...register("department")}
                    onChange={(event) => {
                      setValue("department", event.target.value);
                      setValue("location", "");
                    }}
                  >
                    <option value="">Seleccionar</option>
                    {COLOMBIAN_DEPARTMENTS.map((department) => (
                      <option key={department} value={department}>
                        {department}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Ciudad">
                  <select
                    className="field-control"
                    disabled={!selectedDepartment}
                    {...register("location")}
                  >
                    <option value="">
                      {selectedDepartment
                        ? "Seleccionar ciudad"
                        : "Elige departamento"}
                    </option>
                    {(COLOMBIA_LOCATIONS[selectedDepartment] || []).map(
                      (city) => (
                        <option key={city} value={city}>
                          {city}
                        </option>
                      ),
                    )}
                  </select>
                </Field>
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <Field label="Modalidad">
                  <select className="field-control" {...register("modality")}>
                    <option value="remote">Remoto</option>
                    <option value="hybrid">Híbrido</option>
                    <option value="onsite">Presencial</option>
                  </select>
                </Field>
                <Field label="Tipo de contrato">
                  <select
                    className="field-control"
                    {...register("employment_type")}
                  >
                    <option value="full_time">Tiempo completo</option>
                    <option value="part_time">Medio tiempo</option>
                    <option value="contract">Contrato</option>
                  </select>
                </Field>
                <Field label="Sector laboral">
                  <select
                    className="field-control"
                    {...register("sector", { required: true })}
                  >
                    {JOB_SECTORS.map((sector) => (
                      <option key={sector} value={sector}>
                        {sector}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              <section className="rounded-xl border border-[var(--line)] p-4"><h3 className="mb-2 font-semibold">Idiomas requeridos</h3><LanguagesEditor value={preview.languages || []} onChange={(value) => setValue("languages", value)} required /></section>
              <ScreeningQuestionsEditor
                value={preview.application_questions || []}
                onChange={(value) => setValue("application_questions", value, { shouldDirty: true })}
              />
              <Field label="Beneficios">
                <input
                  className="field-control"
                  placeholder="Separados por coma"
                  {...register("benefits")}
                />
              </Field>
              <footer className="flex justify-end gap-3 border-t border-[var(--line)] pt-5">
                <button
                  type="button"
                  className="button-secondary"
                  onClick={closeForm}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="button-primary"
                  disabled={saving}
                >
                  {editingJob ? <Edit3 size={16} /> : <Plus size={16} />}
                  {saving ? "Guardando…" : editingJob ? "Guardar cambios" : "Publicar vacante"}
                </button>
              </footer>
            </form>
          </section>
        </div>
      ) : null}

      {showPreview ? (
        <div className="fixed inset-0 z-[65] grid place-items-center bg-slate-950/65 p-4 backdrop-blur-sm">
          <section className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] p-5 shadow-2xl">
            <header className="mb-4 flex items-center justify-between">
              <div>
                <p className="section-kicker">Vista del candidato</p>
                <h2 className="mt-1 text-xl font-bold">
                  Previsualización de la vacante
                </h2>
              </div>
              <button
                type="button"
                className="button-secondary !h-10 !w-10 !p-0"
                onClick={() => setShowPreview(false)}
              >
                <X size={18} />
              </button>
            </header>
            <JobPreview values={preview} companyName={company?.name} />
          </section>
        </div>
      ) : null}
      <ConfirmModal
        open={Boolean(pendingDelete)}
        title="Eliminar vacante"
        description={
          pendingDelete
            ? `Se eliminará “${pendingDelete.title}” junto con sus postulaciones y recomendaciones asociadas. Esta acción no se puede deshacer.`
            : ""
        }
        confirmLabel="Sí, eliminar vacante"
        destructive
        loading={deleting}
        onClose={() => setPendingDelete(null)}
        onConfirm={() => pendingDelete && removeJob(pendingDelete)}
      />
      <ConfirmModal
        open={Boolean(pendingSave)}
        title={editingJob ? "Confirmar edición" : "Confirmar publicación"}
        description={
          editingJob
            ? `Se actualizará la vacante “${editingJob.title}” y se recalcularán sus habilidades y recomendaciones.`
            : `Se publicará “${pendingSave?.title || "la vacante"}” y estará disponible para los candidatos. Los seguidores compatibles podrán recibir una notificación.`
        }
        confirmLabel={editingJob ? "Sí, guardar cambios" : "Sí, publicar vacante"}
        loading={saving}
        onClose={() => setPendingSave(null)}
        onConfirm={() => pendingSave && persistJob(pendingSave)}
      />
      {publishedJob && <div className="fixed inset-0 z-[75] grid place-items-center bg-slate-950/65 p-4 backdrop-blur-sm"><section role="dialog" aria-modal="true" aria-labelledby="published-title" className="w-full max-w-md rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl"><h2 id="published-title" className="text-xl font-bold text-[var(--success)]">Vacante publicada correctamente</h2><p className="mt-3 text-sm text-[var(--muted)]">“{publishedJob.title}” ya está activa y disponible para recibir postulaciones.</p><button type="button" className="button-primary mt-5 w-full" onClick={() => setPublishedJob(null)}>Entendido</button></section></div>}
      {reopeningJob && <ReopenJobModal job={reopeningJob} onClose={() => setReopeningJob(null)} onReopened={async (_, mode) => { await load(); setMessage(mode === "continue" ? "Vacante activa. Se conservaron los candidatos y sus seguimientos, sin enviar notificaciones." : "Nueva vacante publicada. El proceso anterior conserva su historial."); }} />}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block text-sm font-semibold text-[var(--muted)]">
      {label}
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

function ScreeningQuestionsEditor({ value, onChange }) {
  const update = (index, changes) =>
    onChange(value.map((question, position) => position === index ? { ...question, ...changes } : question));
  const remove = (index) => onChange(value.filter((_, position) => position !== index));
  const add = () =>
    onChange([
      ...value,
      {
        id: `question_${Date.now()}`,
        prompt: "",
        type: "open",
        required: true,
        options: [],
        keywords: [],
        preferred_options: [],
        option_scores: {},
        positive_adjustment: 3,
        negative_adjustment: 0,
      },
    ]);
  return (
    <section className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">Preguntas antes de postularse</h3>
          <p className="mt-1 max-w-2xl text-sm text-[var(--muted)]">Añade solo las preguntas que ayuden a tomar una decisión. Las respuestas abiertas se revisan manualmente; en las preguntas con opciones puedes indicar cuánto aporta cada respuesta al orden interno.</p>
        </div>
        <button type="button" className="button-outline button-sm" disabled={value.length >= 10} onClick={add}><Plus size={15} />Agregar pregunta</button>
      </div>
      <div className="mt-4 space-y-4">
        {value.map((question, index) => (
          <article key={question.id} className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4">
            <div className="flex items-start gap-3">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--accent)]/10 text-sm font-bold text-[var(--accent)]">{index + 1}</span>
              <div className="grid min-w-0 flex-1 gap-3 md:grid-cols-[1fr_170px]">
                <label className="text-sm font-semibold text-[var(--muted)]">Pregunta<input className="field-control mt-1" value={question.prompt} maxLength={300} placeholder="Ej. ¿Tienes disponibilidad para trabajar los sábados?" onChange={(event) => update(index, { prompt: event.target.value })} /></label>
                <label className="text-sm font-semibold text-[var(--muted)]">Tipo<select className="field-control mt-1" value={question.type} onChange={(event) => update(index, { type: event.target.value, options: [], preferred_options: [], keywords: [], option_scores: {}, positive_adjustment: 3, negative_adjustment: 0 })}><option value="open">Respuesta abierta</option><option value="choice">Elegir una opción</option></select></label>
              </div>
              <button type="button" className="button-ghost button-sm !px-2 text-[var(--error)]" onClick={() => remove(index)} aria-label="Eliminar pregunta"><Trash2 size={16} /></button>
            </div>
            <div className="ml-11 mt-4 space-y-4">
              {question.type === "choice" ? (
                <ChoiceOptions question={question} onChange={(changes) => update(index, changes)} />
              ) : (
                <p className="rounded-lg border border-[var(--line)] bg-[var(--surface-subtle)] px-4 py-3 text-sm leading-6 text-[var(--muted)]">El candidato podrá explicar su respuesta con sus propias palabras. Tu equipo la verá completa y esta pregunta no modificará automáticamente la compatibilidad.</p>
              )}
              <label className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--ink-strong)]"><input type="checkbox" checked={question.required ?? true} onChange={(event) => update(index, { required: event.target.checked })} />Respuesta obligatoria</label>
            </div>
          </article>
        ))}
        {!value.length ? <p className="rounded-lg border border-dashed border-[var(--line)] px-4 py-6 text-center text-sm text-[var(--muted)]">No se pedirán respuestas adicionales.</p> : null}
      </div>
    </section>
  );
}

function ChoiceOptions({ question, onChange }) {
  const options = question.options || [];
  const scoreFor = (option) => {
    if (question.option_scores && Object.hasOwn(question.option_scores, option)) return Number(question.option_scores[option]);
    if ((question.preferred_options || []).includes(option)) return Number(question.positive_adjustment ?? 3);
    return Number(question.negative_adjustment ?? 0);
  };
  const rename = (position, label) => {
    const previous = options[position];
    const nextOptions = options.map((option, index) => index === position ? label : option);
    const nextScores = Object.fromEntries(nextOptions.map((option, index) => [option, index === position ? scoreFor(previous) : scoreFor(option)]).filter(([option]) => option.trim()));
    onChange({ options: nextOptions, option_scores: nextScores, preferred_options: [], keywords: [] });
  };
  const setScore = (option, score) => onChange({ option_scores: { ...(question.option_scores || Object.fromEntries(options.map((item) => [item, scoreFor(item)]))), [option]: Number(score) }, preferred_options: [], keywords: [] });
  const removeOption = (position) => {
    const removed = options[position];
    const nextOptions = options.filter((_, index) => index !== position);
    const nextScores = { ...(question.option_scores || {}) };
    delete nextScores[removed];
    onChange({ options: nextOptions, option_scores: nextScores, preferred_options: [] });
  };
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div><p className="text-sm font-bold text-[var(--ink-strong)]">Opciones de respuesta</p><p className="mt-1 text-xs leading-5 text-[var(--muted)]">Asigna un efecto solo si la respuesta aporta información objetiva. Cero puntos no cambia el orden.</p></div>
        <button type="button" className="button-secondary button-sm" disabled={options.length >= 12} onClick={() => onChange({ options: [...options, ""], option_scores: { ...(question.option_scores || {}) } })}><Plus size={14} />Añadir opción</button>
      </div>
      <div className="mt-3 space-y-2">
        {options.map((option, position) => (
          <div key={position} className="grid gap-2 sm:grid-cols-[1fr_190px_auto] sm:items-center">
            <input className="field-control" value={option} maxLength={120} aria-label={`Opción ${position + 1}`} placeholder={`Opción ${position + 1}`} onChange={(event) => rename(position, event.target.value)} />
            <select className="field-control" aria-label={`Efecto de la opción ${position + 1}`} value={scoreFor(option)} onChange={(event) => setScore(option, event.target.value)}>
              <option value="5">Favorece mucho (+5)</option><option value="3">Favorece (+3)</option><option value="0">No cambia (0)</option><option value="-3">Reduce (-3)</option><option value="-5">Reduce mucho (-5)</option>
            </select>
            <button type="button" className="button-ghost button-sm !px-2 text-[var(--error)]" onClick={() => removeOption(position)} aria-label={`Eliminar opción ${position + 1}`}><Trash2 size={15} /></button>
          </div>
        ))}
        {!options.length ? <p className="rounded-lg border border-dashed border-[var(--line)] px-3 py-4 text-center text-sm text-[var(--muted)]">Añade al menos dos opciones, una por fila.</p> : null}
      </div>
    </div>
  );
}

function JobCard({ job, onEdit, onToggle, onDelete }) {
  const modality =
    { remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" }[
      job.modality
    ] || job.modality;
  const contract =
    {
      full_time: "Tiempo completo",
      part_time: "Medio tiempo",
      contract: "Contrato",
    }[job.employment_type] || job.employment_type;
  return (
    <article className="group flex min-h-[310px] flex-col overflow-hidden rounded-[var(--radius-xl)] border border-[var(--line)] bg-[var(--surface)] transition-colors hover:border-[var(--accent)]">
      <div className="flex-1 p-5">
        <div className="flex items-start justify-between gap-4">
          <span className="grid h-11 w-11 place-items-center rounded-[var(--radius-lg)] bg-[var(--accent)]/10 text-[var(--accent)]">
            <BriefcaseBusiness size={21} />
          </span>
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-bold ${job.status === "active" ? "bg-[var(--success)]/10 text-[var(--success)]" : job.status === "filled" ? "bg-[var(--accent)]/10 text-[var(--accent)]" : "bg-[var(--warning)]/10 text-[var(--warning)]"}`}
          >
            {job.status === "active" ? "Activa" : job.status === "filled" ? "Cubierta" : "Pausada"}
          </span>
        </div>
        <Link
          to={`/vacantes/${job.id}`}
          className="mt-5 block text-lg font-bold hover:text-[var(--accent)] hover:underline"
        >
          {job.title}
        </Link>
        <p className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--muted)]">
          {job.description}
        </p>
        <div className="mt-4 grid gap-2 text-xs text-[var(--muted)] sm:grid-cols-2">
          <span className="inline-flex items-center gap-1.5">
            <MapPin size={14} />
            {[job.location, job.department].filter(Boolean).join(", ") ||
              "Ubicación flexible"}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <CalendarDays size={14} />
            {modality} · {contract}
          </span>
          {job.salary ? (
            <span className="inline-flex items-center gap-1.5">
              <CircleDollarSign size={14} />$
              {Number(job.salary).toLocaleString("es-CO")}
            </span>
          ) : null}
          <span className="font-semibold text-[var(--accent)]">
            {job.sector || "Sector pendiente"}
          </span>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {(job.skills ?? []).slice(0, 5).map((skill) => (
            <span
              key={skill}
              className="rounded-md border border-[var(--line)] bg-[var(--surface-subtle)] px-2 py-1 text-xs text-[var(--muted)]"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>
      <footer className="flex flex-wrap items-center gap-2 border-t border-[var(--line)] bg-[var(--surface-subtle)] p-4">
        <Link
          className="button-primary button-sm"
          to={`/empresa/vacantes/${job.id}/candidatos`}
        >
          <UsersRound size={15} />
          Ver candidatos ({job.applications_count ?? 0})
        </Link>
        <button
          type="button"
          className="button-secondary button-sm"
          onClick={onEdit}
        >
          <Edit3 size={15} />
          Editar
        </button>
        {(
          <button
            type="button"
            className="button-secondary button-sm"
            onClick={onToggle}
          >
            {job.status === "active" ? <PauseCircle size={15} /> : <PlayCircle size={15} />}
            {job.status === "active" ? "Pausar" : job.status === "filled" ? "Reabrir" : "Activar"}
          </button>
        )}
        <button
          type="button"
          className="button-ghost button-sm ml-auto text-[var(--error)]"
          onClick={onDelete}
        >
          <Trash2 size={15} />
        </button>
      </footer>
    </article>
  );
}

function JobPreview({ values, companyName }) {
  const benefits = Array.isArray(values.benefits)
    ? values.benefits
    : String(values.benefits ?? "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
  const modality =
    { remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" }[
      values.modality
    ] ?? "Modalidad flexible";
  const employment =
    {
      full_time: "Tiempo completo",
      part_time: "Medio tiempo",
      contract: "Contrato",
    }[values.employment_type] ?? "Tipo de contrato";
  return (
    <article className="overflow-hidden rounded-[var(--radius-xl)] border border-[var(--line)] bg-[var(--surface-subtle)]">
      <header className="border-b border-[var(--line)] bg-[var(--surface)] p-6">
        <p className="text-xs font-bold uppercase tracking-wide text-[var(--accent)]">
          {companyName || "Tu empresa"}
        </p>
        <h3 className="mt-2 text-2xl font-bold">
          {values.title || "Título de la vacante"}
        </h3>
        <p className="mt-3 text-sm text-[var(--muted)]">
          {[values.location, values.department].filter(Boolean).join(", ") ||
            "Ubicación por definir"}{" "}
          · {modality} · {employment}
        </p>
        {values.salary ? (
          <p className="mt-3 font-bold text-[var(--success)]">
            ${Number(values.salary).toLocaleString("es-CO")} COP
          </p>
        ) : null}
      </header>
      <div className="space-y-5 p-6">
        <div>
          <p className="text-xs font-bold uppercase text-[var(--muted)]">
            Descripción
          </p>
          <p className="mt-2 whitespace-pre-line text-sm leading-6">
            {values.description ||
              "Describe el reto, el equipo y el impacto que tendrá la persona."}
          </p>
        </div>
        <div>
          <p className="text-xs font-bold uppercase text-[var(--muted)]">
            Lo que buscamos
          </p>
          <p className="mt-2 whitespace-pre-line text-sm leading-6">
            {values.requirements || "Los requisitos clave aparecerán aquí."}
          </p>
        </div>
        {values.languages?.length ? <div><h4 className="font-semibold">Idiomas y nivel mínimo</h4><div className="mt-2 space-y-2">{values.languages.map((item, index) => <p className="text-sm capitalize" key={index}>{item.name || "Idioma por definir"} · {languageLevelLabel(item.level)}</p>)}</div></div> : null}
        {values.application_questions?.length ? (
          <div className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4">
            <p className="text-xs font-bold uppercase text-[var(--muted)]">Antes de enviar la postulación</p>
            <p className="mt-1 text-sm text-[var(--muted)]">El candidato responderá {values.application_questions.length} pregunta{values.application_questions.length === 1 ? "" : "s"}.</p>
            <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm">
              {values.application_questions.map((question) => <li key={question.id}>{question.prompt || "Pregunta por completar"}{question.required ? " *" : ""}</li>)}
            </ol>
          </div>
        ) : null}
        {benefits.length ? (
          <div>
            <p className="text-xs font-bold uppercase text-[var(--muted)]">
              Beneficios
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {benefits.map((benefit) => (
                <span
                  key={benefit}
                  className="rounded-full bg-[var(--accent)]/10 px-3 py-1 text-xs font-semibold text-[var(--accent)]"
                >
                  {benefit}
                </span>
              ))}
            </div>
          </div>
        ) : null}
        <button className="button-primary w-full" type="button" disabled>
          Postularme
        </button>
      </div>
    </article>
  );
}
