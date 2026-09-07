import { useEffect, useMemo, useState } from "react";
import {
  Building2,
  BriefcaseBusiness,
  ChevronLeft,
  ChevronRight,
  Search,
  ShieldCheck,
  Trash2,
  UserRound,
  UsersRound,
} from "lucide-react";

import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { ConfirmModal } from "../components/ConfirmModal.jsx";

const tabs = [
  {
    id: "users",
    label: "Candidatos",
    description: "Perfiles y postulaciones",
    icon: UsersRound,
  },
  {
    id: "companies",
    label: "Empresas",
    description: "Organizaciones registradas",
    icon: Building2,
  },
  {
    id: "jobs",
    label: "Vacantes",
    description: "Ofertas y postulaciones",
    icon: BriefcaseBusiness,
  },
];

export function AdminManagementPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [pendingDelete, setPendingDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [pageSize, setPageSize] = useState(10);
  const [page, setPage] = useState(1);

  async function load() {
    setError("");
    setLoading(true);
    try {
      const [usersResponse, companiesResponse, jobsResponse] =
        await Promise.all([
          api.get("/admin/users"),
          api.get("/admin/companies"),
          api.get("/admin/jobs"),
        ]);
      setUsers(usersResponse.data);
      setCompanies(companiesResponse.data);
      setJobs(jobsResponse.data);
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible cargar la administración",
        ),
      );
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function remove(kind, id) {
    setDeleting(true);
    try {
      await api.delete(`/admin/${kind}/${id}`);
      setPendingDelete(null);
      await load();
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "No fue posible eliminar el registro"),
      );
    } finally {
      setDeleting(false);
    }
  }

  const records =
    activeTab === "users"
      ? users.filter((item) => item.role === "candidate")
      : activeTab === "companies"
        ? companies
        : jobs;
  const filtered = useMemo(() => {
    const term = query.toLowerCase().trim();
    if (!term) return records;
    return records.filter((item) =>
      JSON.stringify(item).toLowerCase().includes(term),
    );
  }, [query, records]);
  const activeMeta = tabs.find((tab) => tab.id === activeTab);
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pageCount);
  const visibleRecords = filtered.slice(
    (safePage - 1) * pageSize,
    safePage * pageSize,
  );
  const firstVisible = filtered.length ? (safePage - 1) * pageSize + 1 : 0;
  const lastVisible = Math.min(safePage * pageSize, filtered.length);

  useEffect(() => {
    setPage(1);
  }, [activeTab, query, pageSize]);

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Control de plataforma"
        title="Consola administrativa"
        description="Busca, revisa y administra los recursos principales con una vista más compacta."
      />
      {error ? (
        <p
          role="alert"
          className="rounded-[var(--radius-lg)] border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-sm font-medium text-[var(--error)]"
        >
          {error}
        </p>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-3">
        <Summary
          icon={UsersRound}
          value={users.filter((item) => item.role === "candidate").length}
          label="Candidatos"
          detail="Perfiles registrados"
        />
        <Summary
          icon={Building2}
          value={companies.length}
          label="Organizaciones"
          detail="Empresas registradas"
        />
        <Summary
          icon={BriefcaseBusiness}
          value={jobs.length}
          label="Vacantes"
          detail={`${jobs.reduce((total, item) => total + (item.applications || 0), 0)} postulaciones`}
        />
      </section>

      <section className="grid items-start gap-5 lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="surface-card p-3 lg:sticky lg:top-8">
          <p className="px-3 pb-2 pt-1 text-[11px] font-bold uppercase tracking-[0.16em] text-[var(--muted)]">
            Recursos
          </p>
          <nav className="space-y-1" aria-label="Recursos administrativos">
            {tabs.map(({ id, label, description, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => {
                  setActiveTab(id);
                  setQuery("");
                }}
                aria-pressed={activeTab === id}
                className={`flex w-full items-center gap-3 rounded-[var(--radius-md)] px-3 py-3 text-left transition-colors ${activeTab === id ? "bg-[var(--accent)] text-white" : "text-[var(--ink-strong)] hover:bg-[var(--surface-hover)]"}`}
              >
                <span
                  className={`grid h-9 w-9 shrink-0 place-items-center rounded-[var(--radius-md)] ${activeTab === id ? "bg-white/15" : "bg-[var(--accent)]/10 text-[var(--accent)]"}`}
                >
                  <Icon size={18} />
                </span>
                <span className="min-w-0">
                  <strong className="block text-sm">{label}</strong>
                  <span
                    className={`block truncate text-xs ${activeTab === id ? "text-white/80" : "text-[var(--muted)]"}`}
                  >
                    {description}
                  </span>
                </span>
              </button>
            ))}
          </nav>
          <div className="mt-3 rounded-[var(--radius-md)] bg-[var(--surface-subtle)] p-3">
            <ShieldCheck size={17} className="text-[var(--accent)]" />
            <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
              Las eliminaciones requieren confirmación y respetan las relaciones
              del sistema.
            </p>
          </div>
        </aside>
        <div className="surface-card min-w-0 overflow-hidden !p-0">
          <header className="flex flex-col gap-4 border-b border-[var(--line)] p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="section-kicker">{activeMeta?.label}</p>
              <h2 className="mt-1 text-xl font-bold text-[var(--ink-strong)]">
                {activeMeta?.description}
              </h2>
            </div>
            <label className="relative block sm:w-80">
              <span className="sr-only">Buscar</span>
              <Search
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
                size={17}
              />
              <input
                className="field-control !pl-10"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={`Buscar en ${activeMeta?.label.toLowerCase()}...`}
              />
            </label>
          </header>
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] bg-[var(--surface-subtle)] px-5 py-3 text-xs font-semibold text-[var(--muted)]">
            <span>
              {loading
                ? "Actualizando…"
                : `${firstVisible}-${lastVisible} de ${filtered.length} registros`}
            </span>
            <label className="flex items-center gap-2">
              Mostrar
              <select
                className="field-control input-sm !min-h-8 !w-20 !py-1"
                value={pageSize}
                onChange={(event) => setPageSize(Number(event.target.value))}
              >
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
              </select>
            </label>
          </div>
          <RecordsTable
            kind={activeTab}
            records={visibleRecords}
            currentUserId={user.id}
            onDelete={setPendingDelete}
          />
          <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] px-5 py-4">
            <p className="text-xs text-[var(--muted)]">
              Página {safePage} de {pageCount}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="button-secondary button-sm"
                disabled={safePage <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                <ChevronLeft size={15} />
                Anterior
              </button>
              <button
                type="button"
                className="button-secondary button-sm"
                disabled={safePage >= pageCount}
                onClick={() =>
                  setPage((current) => Math.min(pageCount, current + 1))
                }
              >
                Siguiente
                <ChevronRight size={15} />
              </button>
            </div>
          </footer>
        </div>
      </section>
      <ConfirmModal
        open={Boolean(pendingDelete)}
        title="Confirmar eliminación"
        description={
          pendingDelete
            ? `Se eliminará “${pendingDelete.title}” y toda la información asociada. Esta acción no se puede deshacer.`
            : ""
        }
        confirmLabel="Eliminar registro"
        destructive
        loading={deleting}
        onClose={() => setPendingDelete(null)}
        onConfirm={() =>
          pendingDelete && remove(pendingDelete.kind, pendingDelete.id)
        }
      />
    </div>
  );
}

function Summary({ icon: Icon, value, label, detail }) {
  return (
    <article className="surface-card flex items-center gap-4 p-4">
      <div className="grid h-11 w-11 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-bold text-[var(--ink-strong)]">{value}</p>
        <p className="text-sm font-bold text-[var(--ink-strong)]">{label}</p>
        <p className="text-xs text-[var(--muted)]">{detail}</p>
      </div>
    </article>
  );
}

function RecordsTable({ kind, records, currentUserId, onDelete }) {
  if (!records.length)
    return (
      <div className="py-16 text-center">
        <Search className="mx-auto text-[var(--muted)]" />
        <p className="mt-3 text-sm text-[var(--muted)]">
          No hay registros que coincidan con la búsqueda.
        </p>
      </div>
    );
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[680px] border-collapse text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-[var(--muted)]">
            <th className="px-5 py-3">
              {kind === "users"
                ? "Persona"
                : kind === "companies"
                  ? "Empresa"
                  : "Vacante"}
            </th>
            <th className="px-4 py-3">
              {kind === "users"
                ? "Rol"
                : kind === "companies"
                  ? "Identificación"
                  : "Actividad"}
            </th>
            <th className="px-4 py-3">
              {kind === "users"
                ? "Correo"
                : kind === "companies"
                  ? "Vacantes"
                  : "Habilidades"}
            </th>
            <th className="px-5 py-3 text-right">Acción</th>
          </tr>
        </thead>
        <tbody>
          {records.map((item) => (
            <RecordRow
              key={item.id}
              kind={kind}
              item={item}
              protectedRecord={kind === "users" && item.id === currentUserId}
              onDelete={() =>
                onDelete({
                  kind,
                  id: item.id,
                  title: kind === "users" ? item.name : item.title || item.name,
                })
              }
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RecordRow({ kind, item, protectedRecord, onDelete }) {
  const Icon =
    kind === "users"
      ? UserRound
      : kind === "companies"
        ? Building2
        : BriefcaseBusiness;
  const title = kind === "users" ? item.name : item.title || item.name;
  return (
    <tr className="border-t border-[var(--line)] transition-colors hover:bg-[var(--surface-subtle)]">
      <td className="px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">
            <Icon size={16} />
          </div>
          <div>
            <p className="font-bold text-[var(--ink-strong)]">{title}</p>
            {kind === "companies" ? (
              <p className="max-w-xs truncate text-xs text-[var(--muted)]">
                {item.description || "Sin descripción"}
              </p>
            ) : null}
          </div>
        </div>
      </td>
      <td className="px-4 py-4">
        {kind === "users" ? (
          <RoleBadge role={item.role} />
        ) : kind === "companies" ? (
          <span className="text-[var(--muted)]">NIT {item.nit}</span>
        ) : (
          <span className="font-semibold text-[var(--ink-strong)]">
            {item.applications} postulaciones
          </span>
        )}
      </td>
      <td className="px-4 py-4 text-[var(--muted)]">
        {kind === "users"
          ? item.email
          : kind === "companies"
            ? `${item.jobs} publicadas`
            : item.skills?.slice(0, 3).join(", ") || "Sin habilidades"}
      </td>
      <td className="px-5 py-4 text-right">
        {protectedRecord ? (
          <span className="text-xs font-semibold text-[var(--muted)]">
            Tu cuenta
          </span>
        ) : (
          <button
            type="button"
            className="button-ghost button-sm text-[var(--error)] hover:bg-[var(--error)]/10"
            onClick={onDelete}
          >
            <Trash2 size={15} />
            Eliminar
          </button>
        )}
      </td>
    </tr>
  );
}

function RoleBadge({ role }) {
  const labels = {
    admin: "Administrador",
    company: "Empresa",
    candidate: "Candidato",
  };
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-bold text-[var(--ink-strong)] ${role === "admin" ? "bg-violet-500/15" : role === "company" ? "bg-amber-500/15" : "bg-sky-500/15"}`}
    >
      {labels[role] || role}
    </span>
  );
}
