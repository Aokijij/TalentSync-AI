import { useRecommendations } from "../hooks/useRecommendations.js";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  Clock3,
  Send,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { api } from "../api/client.js";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { MetricCard } from "../components/MetricCard.jsx";
import { Button } from "../components/Button.jsx";
import {
  getProfileCompletion,
  ProfileCompletionRing,
} from "../components/ProfileCompletionRing.jsx";
import { MatchBreakdown } from "../components/MatchBreakdown.jsx";
import { Link } from "react-router-dom";

const candidateStatusLabel = {
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

export function CandidateDashboard() {
  const [recommendations, setRecommendations] = useState([]);
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [message, setMessage] = useState("");
  const [expandedReasons, setExpandedReasons] = useState({});
  const [minCompatibility] = useState(() => {
    const saved = Number(localStorage.getItem("talentsync_recommendation_min"));
    return [40, 50, 60, 70, 80, 90].includes(saved) ? saved : 40;
  });

  const [profile, setProfile] = useState(null);

  async function load() {
    const [
      recommendationsResponse,
      applicationsResponse,
      jobsResponse,
      profileResponse,
    ] = await Promise.all([
      api
        .get("/recommendations/me/jobs", { params: { include_all: true } })
        .catch(() => ({ data: [] })),
      api.get("/applications/me").catch(() => ({ data: [] })),
      api.get("/jobs").catch(() => ({ data: [] })),
      api.get("/profiles/me").catch(() => ({ data: null })),
    ]);
    setRecommendations(recommendationsResponse.data);
    setApplications(applicationsResponse.data);
    setJobs(jobsResponse.data);
    setProfile(profileResponse.data);
  }

  useEffect(() => {
    load();
  }, []);

  const jobsById = useMemo(
    () => new Map(jobs.map((job) => [job.id, job])),
    [jobs],
  );

  const enriched = useRecommendations(
    recommendations,
    minCompatibility,
    false,
  );

  const appliedJobIds = useMemo(
    () => new Set(applications.map((application) => application.job_id)),
    [applications],
  );

  const profileCompletion = useMemo(() => {
    return getProfileCompletion(profile).percentage;
  }, [profile]);

  const recentActivity = useMemo(() => {
    const copy = [...(applications ?? [])];
    copy.sort(
      (a, b) => new Date(b.created_at ?? 0) - new Date(a.created_at ?? 0),
    );
    return copy.slice(0, 5);
  }, [applications]);

  const stats = useMemo(() => {
    const total = applications.length;
    const active = applications.filter(
      (a) => !["rejected", "accepted", "hired"].includes(a.status),
    ).length;
    const accepted = applications.filter((a) =>
      ["accepted", "hired"].includes(a.status),
    ).length;
    const rejected = applications.filter((a) => a.status === "rejected").length;
    return { total, active, accepted, rejected };
  }, [applications]);

  const marketSkills = useMemo(() => {
    const counts = new Map();
    jobs.forEach((job) =>
      (job.skills ?? []).forEach((skill) =>
        counts.set(skill, (counts.get(skill) ?? 0) + 1),
      ),
    );
    return [...counts.entries()]
      .sort((left, right) => right[1] - left[1])
      .slice(0, 6);
  }, [jobs]);

  const pipeline = useMemo(
    () => [
      { label: "Postulaciones", value: applications.length },
      {
        label: "En revisión",
        value: applications.filter((item) =>
          ["seen", "reviewing", "shortlisted"].includes(item.status),
        ).length,
      },
      {
        label: "Entrevistas",
        value: applications.filter(
          (item) =>
            item.interview_at ||
            ["technical_interview", "psychometric_test"].includes(item.status),
        ).length,
      },
      {
        label: "Seleccionado",
        value: applications.filter((item) =>
          ["accepted", "hired"].includes(item.status),
        ).length,
      },
    ],
    [applications],
  );

  function apply(jobId) {
    setMessage("");
    api
      .post("/applications", { job_id: jobId })
      .then(() => api.get("/applications/me"))
      .then(({ data }) => {
        setApplications(data);
        setMessage("Postulacion registrada correctamente");
      })
      .catch(() => {
        setMessage("");
      });
  }

  return (
    <div className="space-y-6">
      <section className="page-hero">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="section-kicker">Espacio candidato</p>
            <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight sm:text-[2.15rem] text-[var(--ink)]">
              Vacantes alineadas a tu perfil
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--muted)]">
              Comparamos tu hoja de vida y habilidades con cada vacante. Completa
              el perfil para mejorar la precisión.
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-3 text-sm">
              <span className="rounded-full border border-[var(--line)] px-3 py-1.5 text-[var(--muted)]">
                Perfil {profileCompletion}%
              </span>
              <span className="rounded-full bg-[var(--accent)]/10 px-3 py-1.5 font-semibold text-[var(--accent)]">
                Perfil analizado
              </span>
            </div>
            <div className="mt-4 h-1.5 rounded-full bg-[var(--muted)]/10">
              <div
                className="h-1.5 rounded-full bg-[var(--accent)] transition-all duration-500"
                style={{ width: `${profileCompletion}%` }}
              />
            </div>
          </div>
          <Link to="/perfil" className="button-secondary shrink-0">
            Mejorar mi perfil <ArrowRight size={16} />
          </Link>
        </div>
        <div className="mt-7 grid gap-3 sm:grid-cols-3">
          <MetricCard
            label="Recomendaciones"
            value={enriched.length}
            detail={`Desde ${minCompatibility}% de compatibilidad`}
            to="/recomendaciones"
          />
          <MetricCard
            label="Postulaciones"
            value={stats.total}
            detail={`${stats.active} activas`}
            to="/postulaciones"
          />
          <MetricCard
            label="Mayor compatibilidad"
            value={`${enriched[0]?.match_percentage?.toFixed?.(0) ?? 0}%`}
            detail="Compatibilidad más alta"
            to="/recomendaciones"
          />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <DashboardAction
            to="/vacantes"
            icon={BriefcaseBusiness}
            title="Explorar oportunidades"
            detail={`${jobs.length} vacantes activas`}
          />
          <DashboardAction
            to="/postulaciones"
            icon={Clock3}
            title="Seguir mis procesos"
            detail={`${stats.active} postulaciones activas`}
          />
          <DashboardAction
            to="/recomendaciones"
            icon={Sparkles}
            title="Ajustar recomendaciones"
            detail={`Porcentaje mínimo: ${minCompatibility}%`}
          />
        </div>
      </section>

      {message ? (
        <p className="rounded-[var(--radius-md)] border border-[var(--success)] bg-[var(--success)]/10 px-4 py-3 text-[var(--success)]">
          {message}
        </p>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[1fr_330px]">
        <div className="surface-card overflow-hidden">
          <div className="flex flex-col gap-3 border-b border-[var(--line)] px-5 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
                <Sparkles size={20} />
              </div>
              <div>
                <h2 className="font-bold text-[var(--ink)]">
                  Recomendaciones inteligentes
                </h2>
                <p className="text-sm text-[var(--muted)]">
                  Oportunidades ordenadas según tu experiencia y habilidades.
                </p>
              </div>
            </div>
            <Link to="/recomendaciones" className="button-secondary button-sm">
              Recomendando desde {minCompatibility}%
            </Link>
          </div>

          <div className="divide-y divide-[var(--line)]">
            {enriched.map((item) => {
              const job = jobsById.get(item.job_id);
              const applied = appliedJobIds.has(item.job_id);
              const isExpanded = expandedReasons[item.id] ?? false;

              const reasonsShort = (item.reasons ?? []).slice(0, 2);
              const reasonsFull = item.reasons ?? [];

              const categoryLabel =
                item.category === "alta"
                  ? "Alta probabilidad"
                  : item.category === "buenas"
                    ? "Buena compatibilidad"
                    : "Con brechas";
              const categoryTone =
                item.category === "alta"
                  ? "border-[var(--success)] bg-[var(--success)]/10 text-[var(--success)]"
                  : item.category === "buenas"
                    ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]"
                    : "border-[var(--warning)] bg-[var(--warning)]/10 text-[var(--warning)]";

              return (
                <article
                  key={item.id}
                  className="grid gap-5 px-5 py-5 transition-colors duration-200 hover:bg-[var(--surface-hover)] lg:grid-cols-[1fr_240px_150px] lg:items-center"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        to={`/vacantes/${item.job_id}`}
                        className="font-semibold text-[var(--ink-strong)] transition-colors hover:text-[var(--accent)] hover:underline"
                      >
                        {job?.title ?? `Vacante #${item.job_id}`}
                      </Link>
                      <span
                        className={`rounded-md border px-2 py-1 text-xs font-semibold ${categoryTone}`}
                      >
                        {categoryLabel}
                      </span>
                      {applied ? (
                        <span className="rounded-md bg-[var(--success)]/10 px-2 py-1 text-xs font-semibold text-[var(--success)]">
                          Postulado
                        </span>
                      ) : null}
                    </div>

                    <p className="mt-1 line-clamp-3 text-sm leading-6 text-[var(--muted)] sm:line-clamp-2">
                      {job?.description ?? reasonsShort.join(". ")}
                    </p>

                    <div className="mt-2 space-y-2">
                      <p
                        className={`text-xs text-[var(--muted)] ${isExpanded ? "" : "line-clamp-2"}`}
                      >
                        {(isExpanded ? reasonsFull : reasonsShort).join(". ")}
                      </p>
                      {reasonsFull.length > 2 ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setExpandedReasons((prev) => ({
                              ...prev,
                              [item.id]: !isExpanded,
                            }))
                          }
                          className="text-[var(--accent)] hover:underline"
                        >
                          <TrendingUp size={14} />
                          {isExpanded ? "Ver menos" : "Cómo mejorar"}
                        </Button>
                      ) : null}
                    </div>
                  </div>

                  <CompatibilityBar value={item.match_percentage} />

                  <Button
                    variant="primary"
                    size="md"
                    disabled={applied}
                    onClick={() => apply(item.job_id)}
                  >
                    <Send size={16} />
                    {applied ? "Enviada" : "Postularme"}
                  </Button>
                  <Link
                    to={`/vacantes/${item.job_id}`}
                    className="text-center text-sm font-semibold text-[var(--accent)] hover:underline"
                  >
                    Ver detalle
                  </Link>
                  {isExpanded ? (
                    <div className="border-t border-[var(--line)] pt-5 lg:col-span-3">
                      <MatchBreakdown
                        skillMatch={item.skill_match_percentage}
                        semanticMatch={item.professional_context_percentage ?? item.semantic_match_percentage}
                        languageMatch={item.language_match_percentage}
                      />
                    </div>
                  ) : null}
                </article>
              );
            })}
            {enriched.length === 0 ? (
              <div className="px-5 py-10 text-sm text-[var(--muted)]">
                No encontramos vacantes con al menos {minCompatibility}% de afinidad para tu
                perfil. Completa tu experiencia y habilidades para mejorar la
                búsqueda.
              </div>
            ) : null}
          </div>
        </div>

        <aside className="space-y-4">
          <div className="surface-card p-5">
            <ProfileCompletionRing profile={profile} compact />
            <Link
              className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
              to="/perfil"
            >
              Completar información <ArrowRight size={15} />
            </Link>
          </div>
          <div className="surface-card p-5">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-[var(--radius-md)] bg-[var(--success)]/10 text-[var(--success)]">
                <BriefcaseBusiness size={18} />
              </div>
              <h2 className="font-bold text-[var(--ink)]">Siguiente paso</h2>
            </div>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
              Sube un CV con texto seleccionable y agrega habilidades para
              recibir recomendaciones más precisas.
            </p>
            <a
              className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline hover-lift"
              href="/perfil"
            >
              Completar perfil
              <ArrowRight size={15} className="text-[var(--accent)]" />
            </a>
          </div>
          <div className="surface-card p-5">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
                <Clock3 size={18} />
              </div>
              <h2 className="font-bold text-[var(--ink)]">
                Actividad reciente
              </h2>
            </div>
            <div className="mt-4 space-y-3">
              {recentActivity.map((application) => (
                <div key={application.id} className="surface-card p-3">
                  <p className="font-semibold text-[var(--ink)]">
                    {jobsById.get(application.job_id)?.title ??
                      `Vacante #${application.job_id}`}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    Estado: {candidateStatusLabel[application.status] || "En revisión"}
                  </p>
                </div>
              ))}
              {applications.length === 0 ? (
                <p className="text-sm text-[var(--muted)]">
                  Aún no tienes postulaciones.
                </p>
              ) : null}
            </div>
          </div>
        </aside>
      </section>
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="surface-card p-5">
          <p className="section-kicker">Tu búsqueda</p>
          <h2 className="mt-1 text-xl font-bold text-[var(--ink-strong)]">
            Progreso del proceso
          </h2>
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {pipeline.map((item) => (
              <div
                key={item.label}
                className="rounded-[var(--radius-lg)] bg-[var(--surface-subtle)] p-4"
              >
                <p className="text-2xl font-bold text-[var(--accent)]">
                  {item.value}
                </p>
                <p className="mt-1 text-xs font-semibold text-[var(--muted)]">
                  {item.label}
                </p>
              </div>
            ))}
          </div>
        </div>
        <div className="surface-card p-5">
          <p className="section-kicker">Mercado</p>
          <h2 className="mt-1 text-xl font-bold text-[var(--ink-strong)]">
            Habilidades más solicitadas
          </h2>
          <div className="mt-5 flex flex-wrap gap-2">
            {marketSkills.map(([skillName, count]) => {
              const owned = (profile?.skills ?? []).some(
                (item) => item.toLowerCase() === skillName.toLowerCase(),
              );
              return (
                <span
                  key={skillName}
                  className={`rounded-full px-3 py-1.5 text-sm font-semibold ${owned ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--surface-subtle)] text-[var(--muted)]"}`}
                >
                  {skillName} · {count}
                  {owned ? " ✓" : ""}
                </span>
              );
            })}
            {!marketSkills.length ? (
              <p className="text-sm text-[var(--muted)]">
                Aparecerán cuando existan vacantes con habilidades detectadas.
              </p>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}

function DashboardAction({ to, icon: Icon, title, detail }) {
  return (
    <Link
      to={to}
      className="group flex items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4 transition-colors hover:bg-[var(--surface-hover)]"
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
        <Icon size={19} />
      </span>
      <span className="min-w-0">
        <strong className="block text-sm text-[var(--ink-strong)]">
          {title}
        </strong>
        <span className="block truncate text-xs text-[var(--muted)]">
          {detail}
        </span>
      </span>
      <ArrowRight
        className="ml-auto text-[var(--muted)] transition-transform group-hover:translate-x-1"
        size={16}
      />
    </Link>
  );
}
