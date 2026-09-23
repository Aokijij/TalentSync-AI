import { useEffect, useMemo, useState } from "react";
import {
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  MapPin,
  Search,
  SlidersHorizontal,
  Sparkles,
  RotateCcw,
} from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import {
  COLOMBIA_LOCATIONS,
  COLOMBIAN_DEPARTMENTS,
} from "../constants/colombianCities.js";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { formatRelativeTime, isWithinDays } from "../utils/dates.js";

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
  const [profileSkills, setProfileSkills] = useState([]);
  const [onlyMySkills, setOnlyMySkills] = useState(false);
  const [minCompatibility, setMinCompatibility] = useState(0);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({
    modality: "",
    department: "",
    location: "",
    sector: "",
    employment_type: "",
    min_salary: "",
    max_salary: "",
    published_days: "",
    sort: "match",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(9);
  const [showFilters, setShowFilters] = useState(false);

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
        api.get("/profiles/me").catch(() => ({ data: { skills: [] } })),
      );
    Promise.all(requests)
      .then(([
        jobsResponse,
        applicationsResponse,
        recommendationsResponse,
        profileResponse,
      ]) => {
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
        setProfileSkills(profileResponse?.data?.skills ?? []);
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
  const salaryCeiling = useMemo(() => {
    const highest = Math.max(...jobs.map((job) => Number(job.salary || 0)), 5000000);
    return Math.ceil(highest / 500000) * 500000;
  }, [jobs]);
  const activeFilterCount = [
    filters.modality,
    filters.department,
    filters.location,
    filters.sector,
    filters.employment_type,
    filters.min_salary,
    filters.max_salary,
    filters.published_days,
    onlyMySkills,
    minCompatibility > 0,
  ].filter(Boolean).length;

  const filteredJobs = useMemo(() => {
    const term = query.toLowerCase().trim();
    const candidateSkills = new Set(
      profileSkills.map((skill) => skill.toLowerCase().trim()),
    );
    return jobs
      .filter((job) => {
        const matchesTerm =
          !term ||
          `${job.title} ${job.company_name} ${job.description} ${job.requirements} ${(job.skills || []).join(" ")}`
            .toLowerCase()
            .includes(term);
        const hasCandidateSkill = (job.skills || []).some((skill) =>
          candidateSkills.has(skill.toLowerCase().trim()),
        );
        return (
          matchesTerm &&
          (!filters.modality || job.modality === filters.modality) &&
          (!filters.employment_type ||
            job.employment_type === filters.employment_type) &&
          (!filters.sector || job.sector === filters.sector) &&
          (!filters.department || job.department === filters.department) &&
          (!filters.location || job.location === filters.location) &&
          (!filters.min_salary || Number(job.salary || 0) >= Number(filters.min_salary)) &&
          (!filters.max_salary || (job.salary != null && Number(job.salary) <= Number(filters.max_salary))) &&
          isWithinDays(job.created_at, Number(filters.published_days || 0)) &&
          (!onlyMySkills || hasCandidateSkill) &&
          (matches[job.id] ?? 0) >= minCompatibility
        );
      })
      .sort((first, second) => {
        if (filters.sort === "newest") return new Date(second.created_at) - new Date(first.created_at);
        if (filters.sort === "oldest") return new Date(first.created_at) - new Date(second.created_at);
        if (filters.sort === "salary_desc") return Number(second.salary || -1) - Number(first.salary || -1);
        if (filters.sort === "salary_asc") return Number(first.salary ?? Number.MAX_SAFE_INTEGER) - Number(second.salary ?? Number.MAX_SAFE_INTEGER);
        return (matches[second.id] ?? -1) - (matches[first.id] ?? -1);
      });
  }, [
    jobs,
    query,
    filters,
    matches,
    profileSkills,
    onlyMySkills,
    minCompatibility,
  ]);

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
                {filteredJobs.length} oportunidades disponibles.
              </p>
            </div>
          </div>
          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
            <label className="relative w-full sm:w-80">
              <Search className="absolute left-3 top-3 text-[var(--muted)]" size={18} />
              <input className="field-control input-md !pl-10" placeholder="Cargo, empresa o habilidad" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} />
            </label>
            <button type="button" className={showFilters ? "button-primary" : "button-secondary"} onClick={() => setShowFilters((current) => !current)} aria-expanded={showFilters}>
              <SlidersHorizontal size={16} /> Filtros{activeFilterCount ? ` (${activeFilterCount})` : ""}<ChevronDown size={15} className={`transition-transform ${showFilters ? "rotate-180" : ""}`} />
            </button>
          </div>
        </div>
        {showFilters ? (
          <div className="mt-5 space-y-5 border-t border-[var(--line)] pt-5">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-[var(--radius-lg)] bg-[var(--surface-subtle)] p-4 sm:col-span-2 lg:col-span-1">
                <p className="mb-3 text-xs font-bold uppercase tracking-wide text-[var(--muted)]">Ubicación</p>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                  <Filter label="Departamento"><select className="field-control input-md" value={filters.department} onChange={(event) => setFilter("department", event.target.value)}><option value="">Todo el país</option>{COLOMBIAN_DEPARTMENTS.map((department) => <option key={department}>{department}</option>)}</select></Filter>
                  <Filter label="Ciudad"><select className="field-control input-md" value={filters.location} disabled={!filters.department} onChange={(event) => setFilter("location", event.target.value)}><option value="">{filters.department ? "Todas" : "Primero elige departamento"}</option>{availableCities.map((city) => <option key={city}>{city}</option>)}</select></Filter>
                </div>
              </div>
              <SalaryRange minimum={Number(filters.min_salary || 0)} maximum={Number(filters.max_salary || salaryCeiling)} ceiling={salaryCeiling} onMinimum={(value) => setFilter("min_salary", value ? String(value) : "")} onMaximum={(value) => setFilter("max_salary", value >= salaryCeiling ? "" : String(value))} />
              <div className="grid gap-3 rounded-[var(--radius-lg)] bg-[var(--surface-subtle)] p-4 sm:grid-cols-2 lg:grid-cols-1 2xl:grid-cols-2">
                <Filter label="Modalidad"><select className="field-control input-md" value={filters.modality} onChange={(event) => setFilter("modality", event.target.value)}><option value="">Todas</option><option value="remote">Remoto</option><option value="hybrid">Híbrido</option><option value="onsite">Presencial</option></select></Filter>
                <Filter label="Contrato"><select className="field-control input-md" value={filters.employment_type} onChange={(event) => setFilter("employment_type", event.target.value)}><option value="">Todos</option><option value="full_time">Tiempo completo</option><option value="part_time">Medio tiempo</option><option value="contract">Contrato</option></select></Filter>
                <Filter label="Sector"><select className="field-control input-md" value={filters.sector} onChange={(event) => setFilter("sector", event.target.value)}><option value="">Todos</option>{availableSectors.map((sector) => <option key={sector}>{sector}</option>)}</select></Filter>
                <Filter label="Publicación"><select className="field-control input-md" value={filters.published_days} onChange={(event) => setFilter("published_days", event.target.value)}><option value="">Cualquier fecha</option><option value="1">Últimas 24 horas</option><option value="7">Última semana</option><option value="30">Último mes</option></select></Filter>
              </div>
            </div>
            <div className="flex flex-col gap-4 border-t border-[var(--line)] pt-4 lg:flex-row lg:items-end lg:justify-between">
              {user?.role === "candidate" ? <div className="flex flex-col gap-3 sm:flex-row sm:items-center"><label className="inline-flex cursor-pointer items-center gap-2 text-sm font-semibold"><input type="checkbox" className="h-4 w-4 accent-[var(--accent)]" checked={onlyMySkills} onChange={(event) => { setOnlyMySkills(event.target.checked); setPage(1); }} />Coincide con mis habilidades</label><Filter label="Compatibilidad mínima"><select className="field-control input-sm w-28" value={minCompatibility} onChange={(event) => { setMinCompatibility(Number(event.target.value)); setPage(1); }}>{[0, 40, 50, 60, 70, 80, 90].map((value) => <option key={value} value={value}>{value}%</option>)}</select></Filter></div> : null}
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end"><Filter label="Ordenar por"><select className="field-control input-sm min-w-44" value={filters.sort} onChange={(event) => setFilter("sort", event.target.value)}>{user?.role === "candidate" ? <option value="match">Mayor compatibilidad</option> : null}<option value="newest">Más recientes</option><option value="oldest">Más antiguas</option><option value="salary_desc">Mayor sueldo</option><option value="salary_asc">Menor sueldo</option></select></Filter><button type="button" className="button-secondary button-sm" onClick={() => { setFilters({ modality: "", department: "", location: "", sector: "", employment_type: "", min_salary: "", max_salary: "", published_days: "", sort: user?.role === "candidate" ? "match" : "newest" }); setQuery(""); setOnlyMySkills(false); setMinCompatibility(0); setPage(1); }}><RotateCcw size={15} />Restablecer</button></div>
            </div>
          </div>
        ) : activeFilterCount ? <button type="button" className="mt-4 text-sm font-semibold text-[var(--accent)] hover:underline" onClick={() => setShowFilters(true)}>{activeFilterCount} filtro{activeFilterCount === 1 ? " activo" : "s activos"} · Ver o cambiar</button> : null}
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
          <Link
            to={`/empresas/${job.company_id}`}
            className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--accent)] hover:underline"
          >
            {job.company_name ?? "Empresa"}
          </Link>
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
        <span className="flex items-center gap-1 font-semibold text-[var(--accent)]"><CalendarDays size={14} />{formatRelativeTime(job.created_at)}</span>
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

function SalaryRange({ minimum, maximum, ceiling, onMinimum, onMaximum }) {
  const step = 250000;
  const safeMinimum = Math.min(minimum, maximum);
  const safeMaximum = Math.max(maximum, minimum);
  const money = (value) => `$${Number(value).toLocaleString("es-CO")}`;
  return (
    <div className="rounded-[var(--radius-lg)] bg-[var(--surface-subtle)] p-4">
      <div className="flex items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wide text-[var(--muted)]">Rango salarial</p><p className="mt-1 text-sm font-semibold text-[var(--ink-strong)]">{money(safeMinimum)} – {safeMaximum >= ceiling ? "Sin límite" : money(safeMaximum)}</p></div><CircleDollarSign size={20} className="text-[var(--accent)]" /></div>
      <label className="mt-4 block text-xs font-semibold text-[var(--muted)]">Desde {money(safeMinimum)}<input className="mt-2 block w-full accent-[var(--accent)]" type="range" min="0" max={ceiling} step={step} value={safeMinimum} onChange={(event) => onMinimum(Math.min(Number(event.target.value), safeMaximum - step))} /></label>
      <label className="mt-3 block text-xs font-semibold text-[var(--muted)]">Hasta {safeMaximum >= ceiling ? "sin límite" : money(safeMaximum)}<input className="mt-2 block w-full accent-[var(--accent)]" type="range" min="0" max={ceiling} step={step} value={safeMaximum} onChange={(event) => onMaximum(Math.max(Number(event.target.value), safeMinimum + step))} /></label>
    </div>
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
