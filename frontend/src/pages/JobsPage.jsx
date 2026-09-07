import { useEffect, useMemo, useState } from "react";
import {
  BriefcaseBusiness,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Search,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import {
  COLOMBIA_LOCATIONS,
  COLOMBIAN_DEPARTMENTS,
} from "../constants/colombianCities.js";
import { JOB_SECTORS } from "../constants/jobSectors.js";

const modalityLabel = {
  remote: "Remoto",
  hybrid: "Híbrido",
  onsite: "Presencial",
};
const contractLabel = {
  full_time: "Tiempo completo",
  part_time: "Medio tiempo",
  contract: "Contrato",
};

export function JobsPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [matches, setMatches] = useState({});
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({
    modality: "",
    department: "",
    location: "",
    sector: "",
    employment_type: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(9);

  useEffect(() => {
    const requests = [
      api.get("/jobs"),
      api.get("/applications/me").catch(() => ({ data: [] })),
    ];
    if (user?.role === "candidate")
      requests.push(
        api
          .get("/recommendations/me/jobs", { params: { include_all: true } })
          .catch(() => ({ data: [] })),
      );
    Promise.all(requests)
      .then(([jobsResponse, applicationsResponse, recommendationsResponse]) => {
        setJobs(jobsResponse.data);
        setApplications(applicationsResponse.data);
        setMatches(
          Object.fromEntries(
            (recommendationsResponse?.data ?? []).map((item) => [
              item.job_id,
              item.match_percentage,
            ]),
          ),
        );
      })
      .catch(() => setJobs([]));
  }, [user?.role]);

  const applied = useMemo(
    () => new Set(applications.map((application) => application.job_id)),
    [applications],
  );
  const availableSectors = useMemo(
    () =>
      JOB_SECTORS.filter((sector) => jobs.some((job) => job.sector === sector)),
    [jobs],
  );
  const availableCities = filters.department
    ? (COLOMBIA_LOCATIONS[filters.department] ?? [])
    : [];

  const filteredJobs = useMemo(() => {
    const term = query.toLowerCase().trim();
    return jobs
      .filter((job) => {
        const matchesTerm =
          !term ||
          `${job.title} ${job.company_name} ${job.description} ${job.requirements} ${(job.skills || []).join(" ")}`
            .toLowerCase()
            .includes(term);
        return (
          matchesTerm &&
          (!filters.modality || job.modality === filters.modality) &&
          (!filters.employment_type ||
            job.employment_type === filters.employment_type) &&
          (!filters.sector || job.sector === filters.sector) &&
          (!filters.department || job.department === filters.department) &&
          (!filters.location || job.location === filters.location)
        );
      })
      .sort(
        (first, second) =>
          (matches[second.id] ?? -1) - (matches[first.id] ?? -1),
      );
  }, [jobs, query, filters, matches]);

  const pages = Math.max(1, Math.ceil(filteredJobs.length / pageSize));
  const visibleJobs = filteredJobs.slice(
    (page - 1) * pageSize,
    page * pageSize,
  );
  const setFilter = (key, value) => {
    setFilters((current) => ({
      ...current,
      [key]: value,
      ...(key === "department" ? { location: "" } : {}),
    }));
    setPage(1);
  };

  useEffect(() => {
    if (page > pages) setPage(pages);
  }, [page, pages]);

  return (
    <div className="space-y-6">
      <section className="surface-card p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-[var(--radius-lg)] bg-[var(--accent)]/10 text-[var(--accent)]">
              <BriefcaseBusiness size={21} />
            </div>
            <div>
              <p className="section-kicker">Mercado laboral</p>
              <h1 className="mt-1 text-2xl font-bold">Explorar vacantes</h1>
              <p className="text-sm text-[var(--muted)]">
                {filteredJobs.length} oportunidades ordenadas por
                compatibilidad.
              </p>
            </div>
          </div>
          <label className="relative w-full sm:w-80">
            <Search
              className="absolute left-3 top-3 text-[var(--muted)]"
              size={18}
            />
            <input
              className="field-control input-md !pl-10"
              placeholder="Cargo, empresa o habilidad"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
            />
          </label>
        </div>
        <div className="mt-5 grid gap-3 border-t border-[var(--line)] pt-5 sm:grid-cols-2 xl:grid-cols-5">
          <Filter label="Departamento">
            <select
              className="field-control input-md"
              value={filters.department}
              onChange={(event) => setFilter("department", event.target.value)}
            >
              <option value="">Todos</option>
              {COLOMBIAN_DEPARTMENTS.map((department) => (
                <option key={department} value={department}>
                  {department}
                </option>
              ))}
            </select>
          </Filter>
          <Filter label="Ciudad">
            <select
              className="field-control input-md"
              value={filters.location}
              disabled={!filters.department}
              onChange={(event) => setFilter("location", event.target.value)}
            >
              <option value="">
                {filters.department
                  ? "Todas las ciudades"
                  : "Elige departamento"}
              </option>
              {availableCities.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
          </Filter>
          <Filter label="Modalidad">
            <select
              className="field-control input-md"
              value={filters.modality}
              onChange={(event) => setFilter("modality", event.target.value)}
            >
              <option value="">Todas</option>
              <option value="remote">Remoto</option>
              <option value="hybrid">Híbrido</option>
              <option value="onsite">Presencial</option>
            </select>
          </Filter>
          <Filter label="Sector laboral">
            <select
              className="field-control input-md"
              value={filters.sector}
              onChange={(event) => setFilter("sector", event.target.value)}
            >
              <option value="">Todos los sectores</option>
              {availableSectors.map((sector) => (
                <option key={sector}>{sector}</option>
              ))}
            </select>
          </Filter>
          <Filter label="Contrato">
            <select
              className="field-control input-md"
              value={filters.employment_type}
              onChange={(event) =>
                setFilter("employment_type", event.target.value)
              }
            >
              <option value="">Todos</option>
              <option value="full_time">Tiempo completo</option>
              <option value="part_time">Medio tiempo</option>
              <option value="contract">Contrato</option>
            </select>
          </Filter>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleJobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            match={matches[job.id]}
            applied={applied.has(job.id)}
            showMatch={user?.role === "candidate"}
          />
        ))}
        {!visibleJobs.length ? (
          <p className="surface-card col-span-full px-5 py-12 text-center text-[var(--muted)]">
            No encontramos vacantes con esos filtros.
          </p>
        ) : null}
      </div>

      {filteredJobs.length ? (
        <nav
          className="surface-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between"
          aria-label="Paginación de vacantes"
        >
          <p className="text-sm text-[var(--muted)]">
            Mostrando {(page - 1) * pageSize + 1}–
            {Math.min(page * pageSize, filteredJobs.length)} de{" "}
            {filteredJobs.length}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-sm font-semibold text-[var(--muted)]">
              Mostrar{" "}
              <select
                className="field-control input-sm ml-2 w-20"
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
              >
                <option value="9">9</option>
                <option value="12">12</option>
                <option value="24">24</option>
              </select>
            </label>
            <button
              className="button-secondary button-sm"
              type="button"
              disabled={page === 1}
              onClick={() => setPage((current) => current - 1)}
            >
              <ChevronLeft size={15} />
              Anterior
            </button>
            <span className="px-2 text-sm font-bold">
              {page} / {pages}
            </span>
            <button
              className="button-secondary button-sm"
              type="button"
              disabled={page === pages}
              onClick={() => setPage((current) => current + 1)}
            >
              Siguiente
              <ChevronRight size={15} />
            </button>
          </div>
        </nav>
      ) : null}
    </div>
  );
}

function JobCard({ job, match, applied, showMatch }) {
  const score = Number(match ?? 0);
  return (
    <article className="surface-card flex flex-col p-5 transition-colors hover:border-[var(--accent)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
            {job.company_name ?? "Empresa"}
          </p>
          <h2 className="mt-1 text-lg font-bold">{job.title}</h2>
        </div>
        {applied ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-[var(--success)]/10 px-2.5 py-1 text-xs font-semibold text-[var(--success)]">
            <CheckCircle2 size={13} />
            Postulado
          </span>
        ) : (
          <span className="rounded-full bg-[var(--accent)]/10 px-2.5 py-1 text-xs font-semibold text-[var(--accent)]">
            {modalityLabel[job.modality] ?? job.modality}
          </span>
        )}
      </div>
      {showMatch ? (
        <div className="mt-4 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="inline-flex items-center gap-1.5 font-semibold text-[var(--muted)]">
              <Sparkles size={15} />
              Compatibilidad
            </span>
            <strong className="text-[var(--accent)]">
              {score.toFixed(0)}%
            </strong>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--line)]">
            <div
              className="h-full rounded-full bg-[var(--accent)]"
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
      ) : null}
      <p className="mt-4 line-clamp-3 text-sm leading-6 text-[var(--muted)]">
        {job.description}
      </p>
      <div className="mt-4 flex flex-wrap gap-3 text-xs text-[var(--muted)]">
        <span className="flex items-center gap-1">
          <MapPin size={14} />
          {[job.location, job.department].filter(Boolean).join(", ") ||
            "Ubicación flexible"}
        </span>
        <span>{contractLabel[job.employment_type] || job.employment_type}</span>
      </div>
      <p className="mt-3 text-sm font-semibold text-[var(--accent)]">
        {job.sector}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {(job.skills || []).slice(0, 5).map((skill) => (
          <span
            key={skill}
            className="rounded-md border border-[var(--line)] px-2 py-1 text-xs text-[var(--muted)]"
          >
            {skill}
          </span>
        ))}
      </div>
      <div className="mt-auto flex items-center justify-between border-t border-[var(--line)] pt-4">
        <strong>
          {job.salary ? `$${job.salary.toLocaleString("es-CO")}` : "A convenir"}
        </strong>
        <Link to={`/vacantes/${job.id}`} className="button-primary button-sm">
          {applied ? "Ver postulación" : "Ver detalle"}
        </Link>
      </div>
    </article>
  );
}

function Filter({ label, children }) {
  return (
    <label className="text-xs font-bold uppercase tracking-wide text-[var(--muted)]">
      <span className="mb-1.5 flex items-center gap-1">
        <SlidersHorizontal size={13} />
        {label}
      </span>
      {children}
    </label>
  );
}
