import { publicationLabel, qualityColor } from "../utils/offerPresentation.js";
import { salaryLabel } from "../utils/offerQuality.js";
import { useEffect, useMemo, useState } from "react";
import {
  BriefcaseBusiness,
  CalendarDays,
  ChevronRight,
  CircleDollarSign,
  Edit3,
  MapPin,
  PauseCircle,
  PlayCircle,
  Plus,
  Search,
  Trash2,
  UsersRound,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { Pagination } from "../components/Pagination.jsx";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { ReopenJobModal } from "../components/ReopenJobModal.jsx";

export function CompanyJobsPage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [company, setCompany] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sectorFilter, setSectorFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [reopeningJob, setReopeningJob] = useState(null);
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

  function openCreate() {
    navigate("/empresa/calidad?nueva=1");
  }

  function editJob(job) {
    navigate(`/empresa/calidad?vacante=${job.id}`);
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
            <option value="draft">Borradores</option>
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
        {filteredJobs.length > pageSize && <div className="surface-card mt-4 p-4"><Pagination page={safePage} total={filteredJobs.length} pageSize={pageSize} onChange={setPage} label="Paginación de vacantes publicadas" /></div>}
      </section>

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
      {reopeningJob && <ReopenJobModal job={reopeningJob} onClose={() => setReopeningJob(null)} onReopened={async (_, mode) => { await load(); setMessage(mode === "continue" ? "Vacante activa. Se conservaron los candidatos y sus seguimientos, sin enviar notificaciones." : "Nueva vacante publicada. El proceso anterior conserva su historial."); }} />}
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
            {job.status === "active" ? "Activa" : job.status === "draft" ? "Borrador" : job.status === "filled" ? "Cubierta" : "Pausada"}
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
        <Link
          className={`company-job-quality ${qualityColor(job.quality_summary)}`}
          to={`/empresa/calidad?vacante=${job.id}`}
          aria-label={`Calidad de la oferta ${job.title}: ${job.quality_summary?.score ?? "sin evaluar"}${job.quality_summary ? "%" : ""}. Revisar calidad`}
        >
          <div className="company-job-quality-heading">
            <span>Calidad de la oferta</span>
            <strong>{job.quality_summary ? `${job.quality_summary.score}%` : "Sin evaluar"}</strong>
          </div>
          {job.quality_summary && <progress aria-label={`Calidad de ${job.title}`} value={job.quality_summary.score} max={100} />}
          <div className="company-job-quality-caption">
            <span>{job.quality_summary?.rating ? `Nivel ${job.quality_summary.rating.code} · ${job.quality_summary.rating.label} · ${publicationLabel(job.status, job.quality_summary.can_publish)}` : "Sin evaluar · Revisar calidad"}</span>
            <ChevronRight size={15} aria-hidden="true" />
          </div>
        </Link>
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
              <CircleDollarSign size={14} />
              {salaryLabel(job)}
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
      <footer className="job-actions-panel">
        <div className="job-actions-main"><Link className="button-primary button-sm" to={`/empresa/talento?job=${job.id}`}><UsersRound size={15} />Ver candidatos <span>{job.applications_count ?? 0}</span></Link><button type="button" className="button-secondary button-sm" onClick={onEdit}><Edit3 size={15} />Editar</button></div>
        <div className="job-actions-secondary"><Link to={`/empresa/calidad?vacante=${job.id}`}>Revisar calidad<ChevronRight size={14} /></Link><button type="button" onClick={onToggle}>{job.status === "active" ? <PauseCircle size={15} /> : <PlayCircle size={15} />}{job.status === "active" ? "Pausar" : job.status === "filled" ? "Reabrir" : "Activar"}</button><button type="button" className="job-action-delete" onClick={onDelete} aria-label={`Eliminar vacante ${job.title}`}><Trash2 size={15} /><span>Eliminar</span></button></div>
      </footer>
    </article>
  );
}
