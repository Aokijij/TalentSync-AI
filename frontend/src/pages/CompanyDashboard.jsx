import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

const statusLabels = {
  submitted: "Nueva",
  seen: "Vista",
  reviewing: "En revisión",
  shortlisted: "Preseleccionada",
  technical_interview: "Entrevista",
  psychometric_test: "Prueba",
  hired: "Contratado",
  accepted: "Aceptada",
  rejected: "Descartada",
};

export function CompanyDashboard() {
  const [company, setCompany] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  useEffect(() => {
    api
      .get("/companies/me")
      .then(async ({ data: companyData }) => {
        setCompany(companyData);
        const { data: allJobs } = await api.get("/jobs", {
          params: { status: "" },
        });
        const ownJobs = allJobs.filter(
          (job) => job.company_id === companyData.id,
        );
        setJobs(ownJobs);
        const responses = await Promise.all(
          ownJobs.map((job) =>
            api.get(`/applications/jobs/${job.id}`).catch(() => ({ data: [] })),
          ),
        );
        setApplications(responses.flatMap((response) => response.data));
      })
      .catch(() => {});
  }, []);
  const stats = useMemo(
    () => ({
      active: jobs.filter((job) => job.status === "active").length,
      applicants: applications.length,
      reviewing: applications.filter((item) =>
        ["reviewing", "submitted", "seen"].includes(item.status),
      ).length,
    }),
    [jobs, applications],
  );
  const funnel = useMemo(
    () => [
      {
        label: "Nuevos",
        value: applications.filter((item) =>
          ["submitted", "seen"].includes(item.status),
        ).length,
      },
      {
        label: "Preselección",
        value: applications.filter((item) =>
          ["reviewing", "shortlisted"].includes(item.status),
        ).length,
      },
      {
        label: "Entrevistas",
        value: applications.filter(
          (item) => item.status === "technical_interview",
        ).length,
      },
      {
        label: "Pruebas",
        value: applications.filter(
          (item) => item.status === "psychometric_test",
        ).length,
      },
      {
        label: "Contratados",
        value: applications.filter((item) =>
          ["accepted", "hired"].includes(item.status),
        ).length,
      },
    ],
    [applications],
  );
  const jobActivity = useMemo(
    () =>
      jobs
        .map((job) => ({
          ...job,
          applications: applications.filter((item) => item.job_id === job.id)
            .length,
        }))
        .sort((left, right) => left.applications - right.applications)
        .slice(0, 4),
    [jobs, applications],
  );
  const funnelMax = Math.max(1, ...funnel.map((item) => item.value));

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Espacio empresa"
        title={`Hola, ${company?.name ?? "empresa"}`}
        description="Prioriza talento, sigue procesos y mantén activas las vacantes correctas."
        actions={
          <>
            <Link to="/empresa/vacantes" className="button-primary">
              <BriefcaseBusiness size={16} />
              Gestionar vacantes
            </Link>
            <Link to="/empresa/talento" className="button-secondary">
              <Sparkles size={16} />
              Buscar talento
            </Link>
          </>
        }
      />
      <section className="grid gap-4 sm:grid-cols-3">
        <Stat
          icon={BriefcaseBusiness}
          label="Vacantes activas"
          value={stats.active}
        />
        <Stat
          icon={UsersRound}
          label="Candidatos en proceso"
          value={stats.applicants}
        />
        <Stat
          icon={ClipboardList}
          label="Pendientes por revisar"
          value={stats.reviewing}
        />
      </section>
      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="surface-card overflow-hidden !p-0">
          <div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-5">
            <div>
              <p className="section-kicker">Actividad de selección</p>
              <h2 className="mt-1 text-xl font-bold text-[var(--ink-strong)]">
                Postulaciones recientes
              </h2>
            </div>
            <Link
              to="/empresa/postulaciones"
              className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--accent)] hover:underline"
            >
              Ver todas
              <ArrowRight size={15} />
            </Link>
          </div>
          <div className="divide-y divide-[var(--line)]">
            {applications.slice(0, 5).map((item) => (
              <div
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-4"
              >
                <div>
                  <p className="font-semibold text-[var(--ink-strong)]">
                    {item.candidate_name || `Candidato #${item.user_id}`}
                  </p>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {item.job_title || "Vacante"}
                  </p>
                </div>
                <span className="rounded-full bg-[var(--accent)]/10 px-3 py-1.5 text-xs font-semibold text-[var(--accent)]">
                  {statusLabels[item.status] || item.status}
                </span>
              </div>
            ))}
            {!applications.length ? (
              <p className="px-5 py-12 text-center text-sm text-[var(--muted)]">
                Aún no tienes postulaciones. Publica una vacante para iniciar el
                proceso.
              </p>
            ) : null}
          </div>
        </div>
        <div className="surface-card p-5">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-[var(--radius-lg)] bg-[var(--success)]/10 text-[var(--success)]">
              <CheckCircle2 size={20} />
            </div>
            <div>
              <h2 className="font-bold text-[var(--ink-strong)]">
                Siguiente acción
              </h2>
              <p className="text-sm text-[var(--muted)]">
                Mantén tu pipeline en movimiento.
              </p>
            </div>
          </div>
          <div className="mt-5 space-y-3">
            <Quick
              to="/empresa/vacantes"
              title="Publicar una vacante"
              detail="Activa el matching semántico."
            />
            <Quick
              to="/empresa/talento"
              title="Revisar talento compatible"
              detail="Prioriza por score y habilidades."
            />
            <Quick
              to="/empresa/postulaciones"
              title="Actualizar procesos"
              detail="Mueve candidatos de etapa."
            />
          </div>
        </div>
      </section>
      <section className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <div className="surface-card p-5">
          <p className="section-kicker">Conversión</p>
          <h2 className="mt-1 text-xl font-bold text-[var(--ink-strong)]">
            Embudo de selección
          </h2>
          <div className="mt-5 space-y-4">
            {funnel.map((item) => (
              <div key={item.label}>
                <div className="mb-1.5 flex justify-between text-sm">
                  <span className="font-semibold text-[var(--muted)]">
                    {item.label}
                  </span>
                  <strong>{item.value}</strong>
                </div>
                <div className="h-2.5 rounded-full bg-[var(--line)]">
                  <div
                    className="h-full rounded-full bg-[var(--accent)]"
                    style={{
                      width: `${item.value ? Math.max(8, (item.value / funnelMax) * 100) : 0}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="surface-card p-5">
          <p className="section-kicker">Atención</p>
          <h2 className="mt-1 text-xl font-bold text-[var(--ink-strong)]">
            Vacantes para impulsar
          </h2>
          <div className="mt-5 space-y-3">
            {jobActivity.map((job) => (
              <Link
                key={job.id}
                to={`/empresa/vacantes/${job.id}/candidatos`}
                className="flex items-center justify-between gap-4 rounded-[var(--radius-lg)] bg-[var(--surface-subtle)] p-4 hover:bg-[var(--surface-hover)]"
              >
                <div>
                  <p className="font-bold text-[var(--ink-strong)]">
                    {job.title}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {job.applications
                      ? `${job.applications} postulaciones`
                      : "Sin postulaciones aún"}
                  </p>
                </div>
                <ArrowRight size={17} className="text-[var(--accent)]" />
              </Link>
            ))}
            {!jobActivity.length ? (
              <p className="text-sm text-[var(--muted)]">
                Publica tu primera vacante para ver recomendaciones.
              </p>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return (
    <article className="surface-card p-5">
      <div className="grid h-10 w-10 place-items-center rounded-[var(--radius-lg)] bg-[var(--accent)]/10 text-[var(--accent)]">
        <Icon size={20} />
      </div>
      <p className="mt-5 text-3xl font-bold tracking-tight text-[var(--ink-strong)]">
        {value}
      </p>
      <p className="mt-1 text-sm text-[var(--muted)]">{label}</p>
    </article>
  );
}
function Quick({ to, title, detail }) {
  return (
    <Link
      to={to}
      className="block rounded-[var(--radius-lg)] bg-[var(--surface-subtle)] p-3 transition-colors hover:bg-[var(--surface-hover)]"
    >
      <p className="font-semibold text-[var(--ink-strong)]">{title}</p>
      <p className="mt-1 text-sm text-[var(--muted)]">{detail}</p>
    </Link>
  );
}
