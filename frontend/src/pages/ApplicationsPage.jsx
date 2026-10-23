import { useEffect, useMemo, useState } from "react";
import {
  CalendarClock,
  Check,
  Clock3,
  FileCheck2,
  SearchCheck,
  XCircle,
} from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import { responseState } from "../utils/responseDeadlines.js";
import { ResponseDeadlineBadge } from "../components/ResponseDeadlinePanel.jsx";
import { InterviewAgenda } from "../components/InterviewAgenda.jsx";
import { activeInterview, interviewDateParts, processDate, upcomingInterviews } from "../utils/interviewAgenda.js";
import { isOpenProcess } from "../utils/dashboardData.js";
import { pageItems, paginationState } from "../utils/pagination.js";
import { Pagination } from "../components/Pagination.jsx";
import { WorkspaceTabs } from "../components/ui/Panel.jsx";

const statusLabel = {
  submitted: "Postulación recibida",
  seen: "Postulación recibida",
  reviewing: "En revisión",
  shortlisted: "En revisión",
  technical_interview: "Entrevista",
  psychometric_test: "Entrevista",
  accepted: "Seleccionado",
  hired: "Seleccionado",
  rejected: "No seleccionado",
};

const progressByStatus = {
  submitted: 0,
  seen: 0,
  reviewing: 1,
  shortlisted: 1,
  technical_interview: 2,
  psychometric_test: 2,
  accepted: 3,
  hired: 3,
  rejected: 3,
};
const steps = [
  { label: "Postulada", icon: FileCheck2 },
  { label: "En revisión", icon: SearchCheck },
  { label: "Entrevista", icon: CalendarClock },
  { label: "Resultado", icon: Check },
];

const interviewStatuses = ["technical_interview", "psychometric_test"];

export function ApplicationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true), [loadError, setLoadError] = useState(""), [retry, setRetry] = useState(0);
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [pendingWithdrawal, setPendingWithdrawal] = useState(null);
  const focusedId = searchParams.get("focus");
  const section = !focusedId && searchParams.get("section") === "interviews" ? "interviews" : "applications";
  function changeSection(value) {
    const next = new URLSearchParams(searchParams);
    next.set("section", value); next.delete("focus");
    setSearchParams(next, { replace: true });
  }

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setLoadError("");
    api.get("/applications/me", { signal: controller.signal, __quiet: true }).then(({ data }) => {
      if (!controller.signal.aborted) setApplications(data);
    }).catch((failure) => { if (!controller.signal.aborted) setLoadError(getApiErrorMessage(failure, "No pudimos cargar tus postulaciones.")); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    const controller = new AbortController();
    // Job metadata must not delay the candidate's processes or agenda.
    api.get("/jobs", { signal: controller.signal, __quiet: true }).then(({ data }) => {
      if (!controller.signal.aborted) setJobs(data);
    }).catch(() => { /* Application records already include job and company titles. */ });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!focusedId || !applications.length) return;
    setFilter("all");
    const index = applications.findIndex((item) => String(item.id) === focusedId);
    if (index >= 0) setPage(Math.floor(index / 8) + 1);
  }, [applications, focusedId]);

  useEffect(() => {
    if (!focusedId || !applications.length) return;
    const timer = window.setTimeout(
      () =>
        document
          .getElementById(`application-${focusedId}`)
          ?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" }),
      80,
    );
    return () => window.clearTimeout(timer);
  }, [applications, focusedId, page]);

  const jobsById = useMemo(
    () => new Map(jobs.map((job) => [job.id, job])),
    [jobs],
  );
  const activeCount = applications.filter(
    isOpenProcess,
  ).length;
  const visibleApplications = applications.filter(
    (item) =>
      filter === "all" ||
      (filter === "active"
        ? isOpenProcess(item)
        : filter === "interview"
          ? isOpenProcess(item) && interviewStatuses.includes(item.status)
          : filter === "finalized"
            ? !isOpenProcess(item)
            : true),
  );
  const paging = paginationState(visibleApplications.length, page, 8);

  async function withdraw(applicationId) {
    await api.post(`/workflow/applications/${applicationId}/withdraw`);
    setApplications((await api.get("/applications/me")).data);
    setPendingWithdrawal(null);
  }

  return (
    <div className="candidate-processes">
      <PageHeader
        kicker="Seguimiento"
        title="Postulaciones y entrevistas"
        description="Sigue tus procesos y organiza tus entrevistas en un solo lugar."
      />
      <WorkspaceTabs id="candidate-processes" label="Seguimiento y agenda" value={section} onChange={changeSection} items={[["applications", `Postulaciones${loading || loadError ? "" : ` (${applications.length})`}`, FileCheck2], ["interviews", `Entrevistas${loading || loadError ? "" : ` (${upcomingInterviews(applications).length})`}`, CalendarClock]]} />
      <div role="tabpanel" id="candidate-processes-panel-interviews" aria-labelledby="candidate-processes-tab-interviews" hidden={section !== "interviews"} tabIndex={0}>
        <InterviewAgenda applications={applications} loading={loading} error={loadError} active={section === "interviews"} onRetry={() => setRetry((value) => value + 1)} />
      </div>
      <div role="tabpanel" className="candidate-applications-panel" id="candidate-processes-panel-applications" aria-labelledby="candidate-processes-tab-applications" hidden={section !== "applications"} tabIndex={0}>
      {loading && <p role="status">Consultando tus postulaciones…</p>}
      {loadError && <p role="alert" className="surface-card p-4">{loadError} <button type="button" className="button-secondary button-sm" onClick={() => setRetry((value) => value + 1)}>Reintentar</button></p>}
      <section className="candidate-application-toolbar" aria-label="Resumen y filtros de postulaciones">
        <dl className="candidate-process-metrics">
          <div><dt><FileCheck2 size={16} aria-hidden="true" />Procesos totales</dt><dd>{loading || loadError ? "—" : applications.length}</dd></div>
          <div className="is-active"><dt><Clock3 size={16} aria-hidden="true" />En curso</dt><dd>{loading || loadError ? "—" : activeCount}</dd></div>
        </dl>
        <label className="candidate-process-state-filter">
          <span>Mostrar estado</span>
          <select className="field-control" value={filter} onChange={(event) => { setFilter(event.target.value); setPage(1); }}>
            <option value="all">Todos</option>
            <option value="active">En curso</option>
            <option value="interview">Con entrevista</option>
            <option value="finalized">Finalizadas</option>
          </select>
        </label>
      </section>

      <section className="space-y-4">
        {pageItems(visibleApplications, page, 8).map((application) => {
          const job = jobsById.get(application.job_id);
          const closed = !isOpenProcess(application);
          const currentIndex = closed ? 3 : progressByStatus[application.status] ?? 0;
          const rejected = application.status === "rejected" || !!application.released_at;
          const withdrawn = application.resolution_reason === "candidate_withdrawn";
          const selected = ["accepted", "hired"].includes(application.status);
          const anotherSelected =
            application.resolution_reason === "another_candidate_selected";
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
                    {processDate(application.created_at)?.toLocaleDateString(
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
                  {withdrawn ? "Retirada por ti" : application.released_at ? "Proceso cerrado" : anotherSelected
                    ? "Finalizada: se seleccionó a otra persona"
                    : statusLabel[application.status] || "En revisión"}
                </span>
              </div>

              <div className="mt-3"><ResponseDeadlineBadge application={application} /></div>
              <div
                className="relative mt-7 grid grid-cols-4 gap-2"
                aria-label={`Progreso: ${statusLabel[application.status] || "En revisión"}`}
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
                        {withdrawn && index === 3 ? "Retirada" : rejected && index === 3
                          ? "No seleccionado"
                          : selected && index === 3
                            ? "Seleccionado"
                            : step.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] pt-4">
                <Link className="button-secondary" to={`/procesos/${application.id}`}>Historial, plazos y feedback</Link>
                <div>
                  {activeInterview(application) ? (
                    <p className="flex items-center gap-2 text-sm font-semibold text-[var(--accent)]">
                      <CalendarClock size={16} />
                      Próxima cita:{" "}
                      {interviewDateParts(application.interview_at).full} · {interviewDateParts(application.interview_at).time} (Colombia)
                    </p>
                  ) : (
                    <p className="text-sm text-[var(--muted)]">
                      {withdrawn ? "Retiraste esta postulación. El historial se conserva." : application.released_at ? "Este proceso ya está cerrado. Consulta el motivo y los mensajes en el seguimiento." : anotherSelected
                        ? "La empresa cubrió esta vacante con otra persona. Esta postulación ya finalizó."
                        : selected
                          ? "Fuiste seleccionado. La empresa se pondrá en contacto contigo para continuar."
                          : "Te notificaremos cuando la empresa actualice el proceso."}
                    </p>
                  )}
                </div>
                {isOpenProcess(application) && (["submitted", "seen"].includes(application.status) || responseState(application) === "paused") ? (
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
        {!loading && !loadError && visibleApplications.length === 0 ? (
          <div className="surface-card py-14 text-center">
            <FileCheck2 className="mx-auto text-[var(--muted)]" />
            <p className="mt-3 text-sm text-[var(--muted)]">
              No hay postulaciones en este estado.
            </p>
          </div>
        ) : null}
      </section>
      {!!visibleApplications.length && <Pagination page={paging.page} total={visibleApplications.length} pageSize={8} onChange={setPage} label="Páginas de postulaciones" busy={loading} />}
      </div>
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
