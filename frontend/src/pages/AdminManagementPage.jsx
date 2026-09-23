import { useEffect, useMemo, useState } from "react";
import {
  Building2,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  FileSpreadsheet,
  Search,
  ShieldCheck,
  Trash2,
  UploadCloud,
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
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);

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

  async function downloadImportTemplate() {
    setError("");
    try {
      const response = await api.get("/admin/jobs/import-template", {
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "plantilla-vacantes-talentsync.csv";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(
        getApiErrorMessage(requestError, "No fue posible descargar la plantilla"),
      );
    }
  }

  async function importJobs(event) {
    event.preventDefault();
    const formElement = event.currentTarget;
    if (!importFile) {
      setError("Selecciona un archivo CSV o XLSX para continuar");
      return;
    }
    setError("");
    setImportResult(null);
    setImporting(true);
    try {
      const form = new FormData();
      form.append("file", importFile);
      const { data } = await api.post("/admin/jobs/import", form);
      setImportResult(data);
      setImportFile(null);
      formElement.reset();
      await load();
    } catch (requestError) {
      const detail = requestError?.response?.data?.detail;
      if (detail?.message) {
        setError(detail.message);
        setImportResult({
          created: 0,
          updated: 0,
          companies_created: 0,
          rejected: detail.errors?.length || 0,
          errors: detail.errors || [],
        });
      } else {
        setError(
          getApiErrorMessage(requestError, "No fue posible importar las vacantes"),
        );
      }
    } finally {
      setImporting(false);
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
          {activeTab === "jobs" ? (
            <JobImportPanel
              file={importFile}
              importing={importing}
              result={importResult}
              onFile={setImportFile}
              onImport={importJobs}
              onDownload={downloadImportTemplate}
            />
          ) : null}
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

function JobImportPanel({ file, importing, result, onFile, onImport, onDownload }) {
  return (
    <section className="border-b border-[var(--line)] bg-[var(--accent)]/[0.04] p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="flex max-w-2xl items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
            <FileSpreadsheet size={20} />
          </span>
          <div>
            <h3 className="font-bold text-[var(--ink-strong)]">
              Importar catálogo autorizado
            </h3>
            <p className="mt-1 text-sm leading-5 text-[var(--muted)]">
              Carga hasta 2.000 vacantes desde CSV o Excel. TalentSync identifica cada
              oferta por su fuente e ID externo para actualizarla sin duplicados.
            </p>
            <p className="mt-2 text-xs text-[var(--muted)]">
              Separa habilidades y beneficios con |. Para idiomas usa, por ejemplo,
              inglés:B2|español:C1.
            </p>
          </div>
        </div>
        <button type="button" className="button-secondary button-sm shrink-0" onClick={onDownload}>
          <Download size={15} />
          Descargar plantilla
        </button>
      </div>
      <form className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={onImport}>
        <label className="min-w-0 flex-1 text-xs font-bold text-[var(--muted)]">
          Archivo de vacantes
          <input
            type="file"
            accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            className="field-control mt-1.5 file:mr-3 file:rounded-lg file:border-0 file:bg-[var(--accent)]/10 file:px-3 file:py-1.5 file:font-semibold file:text-[var(--accent)]"
            onChange={(event) => onFile(event.target.files?.[0] || null)}
          />
        </label>
        <button type="submit" className="button-primary shrink-0" disabled={importing || !file}>
          <UploadCloud size={17} />
          {importing ? "Importando…" : "Importar vacantes"}
        </button>
      </form>
      {result ? (
        <div className="mt-4 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4">
          <div className="flex items-center gap-2 text-sm font-bold text-[var(--ink-strong)]">
            <CheckCircle2 size={17} className="text-[var(--success)]" />
            Resultado de la importación
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <ImportMetric label="Creadas" value={result.created} />
            <ImportMetric label="Actualizadas" value={result.updated} />
            <ImportMetric label="Empresas nuevas" value={result.companies_created} />
            <ImportMetric label="Rechazadas" value={result.rejected} warning={result.rejected > 0} />
          </div>
          {result.errors?.length ? (
            <details className="mt-3 text-sm text-[var(--muted)]">
              <summary className="cursor-pointer font-semibold text-[var(--ink-strong)]">
                Ver errores de las filas
              </summary>
              <ul className="mt-2 max-h-36 space-y-1 overflow-y-auto pl-5">
                {result.errors.map((item, index) => (
                  <li key={`${item.row}-${index}`} className="list-disc">
                    Fila {item.row}: {item.detail}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function ImportMetric({ label, value, warning = false }) {
  return (
    <div className="rounded-xl bg-[var(--surface-subtle)] px-3 py-2">
      <strong className={warning ? "text-[var(--error)]" : "text-[var(--accent)]"}>
        {value || 0}
      </strong>
      <span className="ml-1.5 text-xs text-[var(--muted)]">{label}</span>
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
            {item.source_name ? (
              <p className="mt-0.5 text-xs font-semibold text-[var(--accent)]">
                Fuente: {item.source_name}
              </p>
            ) : null}
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
