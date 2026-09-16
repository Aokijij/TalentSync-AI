import { useRecommendations } from "../hooks/useRecommendations.js";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  Send,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { SkillRadarChart } from "../components/SkillRadarChart.jsx";
import { MatchBreakdown } from "../components/MatchBreakdown.jsx";

export function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState([]);
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [profile, setProfile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [minCompatibility, setMinCompatibility] = useState(() => {
    const saved = Number(localStorage.getItem("talentsync_recommendation_min"));
    return [40, 50, 60, 70, 80, 90].includes(saved) ? saved : 40;
  });

  const [expandedReasons, setExpandedReasons] = useState({});

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [
        recommendationsResponse,
        applicationsResponse,
        jobsResponse,
        profileResponse,
      ] = await Promise.all([
        api.get("/recommendations/me/jobs", { params: { include_all: true } }),
        api.get("/applications/me"),
        api.get("/jobs"),
        api.get("/profiles/me"),
      ]);
      setRecommendations(recommendationsResponse.data);
      setApplications(applicationsResponse.data);
      setJobs(jobsResponse.data);
      setProfile(profileResponse.data);
    } catch (err) {
      setError("No fue posible cargar las recomendaciones");
      console.error("Failed to load recommendations:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const jobsById = useMemo(
    () => new Map(jobs.map((job) => [job.id, job])),
    [jobs],
  );

  const enriched = useRecommendations(recommendations, minCompatibility, false);

  function changeMinimum(value) {
    const next = Number(value);
    setMinCompatibility(next);
    localStorage.setItem("talentsync_recommendation_min", String(next));
  }

  const appliedJobIds = useMemo(
    () => new Set(applications.map((application) => application.job_id)),
    [applications],
  );

  async function apply(jobId) {
    setMessage("");
    await api.post("/applications", { job_id: jobId });
    setMessage("Postulación registrada correctamente");
    const { data } = await api.get("/applications/me");
    setApplications(data);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Recomendaciones"
        title="Empleos sugeridos para tu perfil"
        description="Cada vacante muestra compatibilidad, habilidades coincidentes y una guía para mejorar."
      />

      {error && (
        <p className="rounded-[var(--radius-lg)] border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-sm text-[var(--error)]">
          {error}
        </p>
      )}

      {message && (
        <p className="rounded-[var(--radius-md)] border border-[var(--success)] bg-[var(--success)]/10 px-3 py-2 text-sm text-[var(--success)]">
          {message}
        </p>
      )}

      {loading && (
        <section className="surface-card">
          <div className="px-5 py-8 text-center">
            <div className="animate-pulse inline-flex items-center gap-4">
              <div className="h-8 w-8 rounded-full bg-[var(--accent)]/20"></div>
              <div className="h-8 w-8 rounded-full bg-[var(--accent)]/20"></div>
              <div className="h-8 w-8 rounded-full bg-[var(--accent)]/20"></div>
            </div>
            <p className="mt-4 text-sm text-[var(--muted)]">
              Cargando recomendaciones...
            </p>
          </div>
        </section>
      )}

      {!loading && !error && (
        <section className="surface-card">
          <div className="flex flex-col gap-3 border-b border-[var(--line)] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <BriefcaseBusiness className="text-[var(--success)]" size={20} />
              <div>
                <h2 className="font-semibold text-[var(--ink)]">
                  Lista de empleo recomendada
                </h2>
                <p className="text-sm text-[var(--muted)]">
                  Ordenadas por compatibilidad con tu trayectoria y habilidades.
                </p>
              </div>
            </div>
            <label className="flex items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] px-4 py-2 text-sm font-semibold text-[var(--muted)]">
              Recomendar desde
              <select
                className="field-control input-sm w-24"
                value={minCompatibility}
                onChange={(event) => changeMinimum(event.target.value)}
              >
                {[40, 50, 60, 70, 80, 90].map((value) => (
                  <option key={value} value={value}>
                    {value}%
                  </option>
                ))}
              </select>
            </label>
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
                  ? "bg-[var(--success)]/10 border-[var(--success)]"
                  : item.category === "buenas"
                    ? "bg-[var(--accent)]/10 border-[var(--accent)]"
                    : "bg-[var(--warning)]/10 border-[var(--warning)]";

              return (
                <article
                  key={item.id}
                  className="grid gap-5 p-5 lg:grid-cols-[1fr_240px_180px] lg:items-center"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-[var(--ink)]">
                        {job?.title ?? `Vacante #${item.job_id}`}
                      </p>
                      <span
                        className={`rounded-[var(--radius-md)] border px-2 py-1 text-xs font-semibold text-[var(--ink)] ${categoryTone}`}
                      >
                        {categoryLabel}
                      </span>
                      {applied ? (
                        <span className="rounded-[var(--radius-md)] bg-[var(--success)]/10 px-2 py-1 text-xs font-semibold text-[var(--ink)]">
                          Postulado
                        </span>
                      ) : null}
                    </div>

                    <p className="mt-1 line-clamp-2 text-sm text-[var(--muted)]">
                      {job?.description ?? reasonsShort.join(". ")}
                    </p>

                    <div className="mt-2 space-y-2">
                      <p
                        className={`text-xs text-[var(--muted)] ${isExpanded ? "" : "line-clamp-2"}`}
                      >
                        {(isExpanded ? reasonsFull : reasonsShort).join(". ")}
                      </p>
                      {reasonsFull.length > 2 ? (
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedReasons((prev) => ({
                              ...prev,
                              [item.id]: !isExpanded,
                            }))
                          }
                          className="inline-flex items-center gap-2 text-xs font-semibold text-[var(--success)] hover:underline hover-lift"
                        >
                          <TrendingUp
                            size={14}
                            className="text-[var(--success)]"
                          />
                          {isExpanded ? "Ver menos" : "Cómo mejorar"}
                        </button>
                      ) : null}
                    </div>

                    <div className="mt-3">
                      <Link
                        to={`/vacantes/${item.job_id}`}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline hover-lift"
                      >
                        Ver detalle
                        <ArrowRight
                          size={16}
                          className="text-[var(--accent)]"
                        />
                      </Link>
                    </div>
                  </div>

                  <CompatibilityBar value={item.match_percentage} />

                  <div className="flex items-center justify-end">
                    <button
                      type="button"
                      disabled={applied}
                      onClick={() => apply(item.job_id)}
                      className="inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--success)] px-3 py-2 text-sm font-semibold text-white hover:bg-[var(--success)]/90 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <Send size={16} className="text-white" />
                      {applied ? "Enviada" : "Postularme"}
                    </button>
                  </div>
                  {isExpanded ? (
                    <div className="grid gap-6 border-t border-[var(--line)] pt-5 lg:col-span-3 lg:grid-cols-2">
                      <MatchBreakdown
                        skillMatch={item.skill_match_percentage}
                        semanticMatch={item.professional_context_percentage ?? item.semantic_match_percentage}
                        languageMatch={item.language_match_percentage}
                      />
                      <SkillRadarChart
                        candidateSkills={profile?.skills ?? []}
                        requiredSkills={job?.skills ?? []}
                        matchPercentage={item.match_percentage}
                      />
                    </div>
                  ) : null}
                </article>
              );
            })}

            {enriched.length === 0 ? (
              <div className="px-5 py-10 text-center text-[var(--muted)]">
                <Sparkles
                  size={20}
                  className="mx-auto mb-3 text-[var(--accent)]"
                />
                No hay vacantes que alcancen el {minCompatibility}% de
                compatibilidad. Puedes reducir el porcentaje o completar mejor
                tu experiencia y habilidades.
              </div>
            ) : null}
          </div>
        </section>
      )}

      <section className="surface-card p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Sparkles size={20} className="text-[var(--accent)]" />
            <div>
              <h2 className="font-semibold text-[var(--ink)]">
                Siguiente paso
              </h2>
              <p className="text-sm text-[var(--muted)]">
                Completa tu perfil para subir el porcentaje de compatibilidad.
              </p>
            </div>
          </div>
          <Link
            to="/perfil"
            className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline hover-lift"
          >
            Completar perfil
            <ArrowRight size={15} className="text-[var(--accent)]" />
          </Link>
        </div>
      </section>
    </div>
  );
}
