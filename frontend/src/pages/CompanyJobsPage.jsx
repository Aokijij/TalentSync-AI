import { useEffect, useMemo, useState } from "react";
import {
  BriefcaseBusiness,
  CalendarDays,
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
    const payload = formPayload(values);
    if (editingJob) setPendingSave(payload);
    else persistJob(payload);
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
        await api.post("/jobs", payload);
        setMessage("Vacante publicada y analizada por el motor NLP.");
      }
      closeForm();
      await load();
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "No fue posible guardar la vacante"),
      );
    } finally {
      setSaving(false);
    }
  }

  function openCreate() {
    setEditingJob(null);
    setPendingSave(null);
    setShowPreview(false);
    reset(NEW_JOB_DEFAULTS);
    setShowModal(true);
  }

  function editJob(job) {
    setEditingJob(job);
    setPendingSave(null);
    setShowPreview(false);
    reset({
      ...job,
      department: job.department || departmentForCity(job.location),
      benefits: (job.benefits || []).join(", "),
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
          {filteredJobs.map((job) => (
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
              onSubmit={handleSubmit(submitJob)}
            >
              <Field label="Cargo">
                <input
                  className="field-control"
                  placeholder="Ej. Analista financiero"
                  {...register("title", { required: true })}
                />
              </Field>
              <div className="grid gap-5 md:grid-cols-2">
                <Field label="Descripción">
                  <textarea
                    className="field-control min-h-52 resize-y"
                    placeholder="Responsabilidades, equipo e impacto del cargo"
                    {...register("description", { required: true })}
                  />
                </Field>
                <Field label="Requisitos y habilidades">
                  <textarea
                    className="field-control min-h-52 resize-y"
                    placeholder="Formación, experiencia y conocimientos requeridos"
                    {...register("requirements", { required: true })}
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
                  {editingJob ? "Guardar cambios" : "Publicar vacante"}
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
        title="Confirmar edición"
        description={
          editingJob
            ? `Se actualizará la vacante “${editingJob.title}” y se recalcularán sus habilidades y recomendaciones.`
            : ""
        }
        confirmLabel="Sí, guardar cambios"
        loading={saving}
        onClose={() => setPendingSave(null)}
        onConfirm={() => pendingSave && persistJob(pendingSave)}
      />
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
            className={`rounded-full px-2.5 py-1 text-xs font-bold ${job.status === "active" ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--warning)]/10 text-[var(--warning)]"}`}
          >
            {job.status === "active" ? "Activa" : "Pausada"}
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
          Ver ranking ({job.applications_count ?? 0})
        </Link>
        <button
          type="button"
          className="button-secondary button-sm"
          onClick={onEdit}
        >
          <Edit3 size={15} />
          Editar
        </button>
        <button
          type="button"
          className="button-secondary button-sm"
          onClick={onToggle}
        >
          {job.status === "active" ? (
            <PauseCircle size={15} />
          ) : (
            <PlayCircle size={15} />
          )}
          {job.status === "active" ? "Pausar" : "Activar"}
        </button>
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
