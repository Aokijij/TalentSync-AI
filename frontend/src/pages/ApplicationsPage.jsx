import { useEffect, useMemo, useState } from "react";
import {
  CalendarClock,
  Check,
  Clock3,
  Eye,
  FileCheck2,
  SearchCheck,
  XCircle,
} from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { ConfirmModal } from "../components/ConfirmModal.jsx";

const statusLabel = {
  submitted: "Enviada",
  seen: "Vista por la empresa",
  reviewing: "En revisión",
  shortlisted: "Preseleccionada",
  technical_interview: "Entrevista técnica",
  psychometric_test: "Prueba psicotécnica",
  accepted: "Aceptada",
  hired: "Contratado",
  rejected: "Descartada",
};

const progressByStatus = {
  submitted: 0,
  seen: 1,
  reviewing: 2,
  shortlisted: 2,
  technical_interview: 2,
  psychometric_test: 2,
  accepted: 3,
  hired: 3,
  rejected: 3,
};
const steps = [
  { label: "Enviada", icon: FileCheck2 },
  { label: "Vista", icon: Eye },
  { label: "En proceso", icon: SearchCheck },
  { label: "Resultado", icon: Check },
];

export function ApplicationsPage() {
  const [searchParams] = useSearchParams();
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState("all");
  const [pendingWithdrawal, setPendingWithdrawal] = useState(null);
  const focusedId = searchParams.get("focus");

  useEffect(() => {
    Promise.all([
      api.get("/applications/me").catch(() => ({ data: [] })),
      api.get("/jobs").catch(() => ({ data: [] })),
    ]).then(([applicationsResponse, jobsResponse]) => {
      setApplications(applicationsResponse.data);
      setJobs(jobsResponse.data);
    });
  }, []);

  useEffect(() => {
    if (!focusedId || !applications.length) return;
    window.setTimeout(
      () =>
        document
          .getElementById(`application-${focusedId}`)
          ?.scrollIntoView({ behavior: "smooth", block: "center" }),
      80,
    );
  }, [applications, focusedId]);

  const jobsById = useMemo(
    () => new Map(jobs.map((job) => [job.id, job])),
    [jobs],
  );
  const activeCount = applications.filter(
    (item) => !["rejected", "accepted", "hired"].includes(item.status),
  ).length;
  const visibleApplications = applications.filter(
    (item) =>
      filter === "all" ||
      (filter === "active"
        ? !["rejected", "accepted", "hired"].includes(item.status)
        : item.status === filter),
  );

  async function withdraw(applicationId) {
    await api.delete(`/applications/${applicationId}`);
    setApplications((current) =>
      current.filter((item) => item.id !== applicationId),
    );
    setPendingWithdrawal(null);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Seguimiento"
        title="Pipeline de postulaciones"
        description="Sigue cada proceso desde el envío hasta la decisión final en una línea de tiempo clara."
      />
      <section className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-center">
        <div className="grid grid-cols-2 gap-3 sm:max-w-sm">
          <div className="surface-card px-4 py-3">
            <p className="text-2xl font-bold text-[var(--ink-strong)]">
              {applications.length}
            </p>
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
              Procesos totales
            </p>
          </div>
          <div className="surface-card px-4 py-3">
            <p className="text-2xl font-bold text-[var(--accent)]">
              {activeCount}
            </p>
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
              En curso
            </p>
          </div>
        </div>
        <label className="text-sm font-semibold text-[var(--muted)]">
          Mostrar estado
          <select
            className="field-control mt-1 sm:w-56"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
          >
            <option value="all">Todos</option>
            <option value="active">En curso</option>
            <option value="submitted">Enviadas</option>
            <option value="seen">Vistas</option>
            <option value="shortlisted">Preseleccionadas</option>
            <option value="technical_interview">Entrevista técnica</option>
            <option value="psychometric_test">Prueba psicotécnica</option>
            <option value="hired">Contratado</option>
            <option value="rejected">Descartadas</option>
          </select>
        </label>
      </section>

      <section className="space-y-4">
        {visibleApplications.map((application) => {
          const job = jobsById.get(application.job_id);
          const currentIndex = progressByStatus[application.status] ?? 0;
          const rejected = application.status === "rejected";
          return (
            <article
              id={`application-${application.id}`}
              key={application.id}
              className={`surface-card p-5 sm:p-6 ${String(application.id) === focusedId ? "ring-2 ring-[var(--accent)] ring-offset-4 ring-offset-[var(--canvas)]" : ""}`}
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <Link
                    to={`/vacantes/${application.job_id}`}
                    className="text-lg font-bold text-[var(--ink-strong)] hover:text-[var(--accent)] hover:underline"
                  >
                    {job?.title ??
                      application.job_title ??
                      `Vacante #${application.job_id}`}
                  </Link>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {application.company_name ?? job?.company_name ?? "Empresa"}{" "}
                    · Aplicaste el{" "}
                    {new Date(application.created_at).toLocaleDateString(
                      "es-CO",
                      { day: "numeric", month: "long", year: "numeric" },
                    )}
                  </p>
                </div>
                <span
                  className={`inline-flex w-fit items-center gap-2 rounded-full px-3 py-1.5 text-sm font-bold ${rejected ? "bg-[var(--error)]/10 text-[var(--error)]" : currentIndex === 3 ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--accent)]/10 text-[var(--accent)]"}`}
                >
                  {rejected ? <XCircle size={16} /> : <Clock3 size={16} />}Etapa
                  actual:{" "}
                  {application.pipeline_stage_title ||
                    statusLabel[application.status] ||
                    application.status}
                </span>
              </div>

              <div
                className="relative mt-7 grid grid-cols-4 gap-2"
                aria-label={`Progreso: ${application.pipeline_stage_title || statusLabel[application.status] || application.status}`}
              >
                <div className="absolute left-[12.5%] right-[12.5%] top-5 h-1 rounded-full bg-[var(--line)]" />
                <div
                  className={`absolute left-[12.5%] top-5 h-1 rounded-full transition-all ${rejected ? "bg-[var(--error)]" : "bg-[var(--accent)]"}`}
                  style={{ width: `${(currentIndex / 3) * 75}%` }}
                />
                {steps.map((step, index) => {
                  const Icon = rejected && index === 3 ? XCircle : step.icon;
                  const reached = index <= currentIndex;
                  return (
                    <div
                      key={step.label}
                      className="relative z-10 flex min-w-0 flex-col items-center text-center"
                    >
                      <span
                        className={`grid h-10 w-10 place-items-center rounded-full border-4 border-[var(--surface)] ${reached ? (rejected && index === 3 ? "bg-[var(--error)] text-white" : "bg-[var(--accent)] text-white") : "bg-[var(--line)] text-[var(--muted)]"}`}
                      >
                        <Icon size={16} />
                      </span>
                      <span
                        className={`mt-2 text-[11px] font-bold sm:text-xs ${reached ? "text-[var(--ink-strong)]" : "text-[var(--muted)]"}`}
                      >
                        {rejected && index === 3 ? "Descartada" : step.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] pt-4">
                <div>
                  {application.interview_at ? (
                    <p className="flex items-center gap-2 text-sm font-semibold text-[var(--accent)]">
                      <CalendarClock size={16} />
                      Próxima cita:{" "}
                      {new Date(application.interview_at).toLocaleString(
                        "es-CO",
                      )}
                    </p>
                  ) : (
                    <p className="text-sm text-[var(--muted)]">
                      Te notificaremos cuando la empresa actualice el proceso.
                    </p>
                  )}
                </div>
                {["submitted", "seen"].includes(application.status) ? (
                  <button
                    className="text-sm font-semibold text-[var(--error)] hover:underline"
                    type="button"
                    onClick={() => setPendingWithdrawal(application)}
                  >
                    Retirar postulación
                  </button>
                ) : null}
              </div>
            </article>
          );
        })}
        {visibleApplications.length === 0 ? (
          <div className="surface-card py-14 text-center">
            <FileCheck2 className="mx-auto text-[var(--muted)]" />
            <p className="mt-3 text-sm text-[var(--muted)]">
              No hay postulaciones en este estado.
            </p>
          </div>
        ) : null}
      </section>
      <ConfirmModal
        open={Boolean(pendingWithdrawal)}
        title="Retirar postulación"
        description={
          pendingWithdrawal
            ? `Dejarás de participar en el proceso de ${jobsById.get(pendingWithdrawal.job_id)?.title || pendingWithdrawal.job_title || "esta vacante"}.`
            : ""
        }
        confirmLabel="Retirar postulación"
        destructive
        onClose={() => setPendingWithdrawal(null)}
        onConfirm={() => pendingWithdrawal && withdraw(pendingWithdrawal.id)}
      />
    </div>
  );
}
