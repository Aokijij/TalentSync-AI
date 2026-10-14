import { SkillRadarChart } from "../components/SkillRadarChart.jsx";
import { RequirementSupport } from "../components/RequirementSupport.jsx";
import { SearchPreferences } from "../components/SearchPreferences.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { readRecommendationSettings, saveRecommendationSetting } from "../utils/recommendationSettings.js";
import { orderRecommendations } from "../utils/recommendationOrder.js";
import { RecommendationControls } from "../components/RecommendationControls.jsx";
import { useRecommendations } from "../hooks/useRecommendations.js";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  ChevronLeft,
  ChevronRight,
  Send,
  Sparkles,
  TrendingUp,
  Building2,
  MapPin,
} from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { getRecommendations } from "../api/recommendations.js";
import "../styles/recommendations.css";
import { PageHeader } from "../components/PageHeader.jsx";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { VacancyLearningPanel } from "../components/VacancyLearningPanel.jsx";
import { JobInterestButtons } from "../components/JobInterests.jsx";
import { useJobInterests } from "../hooks/useJobInterests.js";
import { searchJob, visibleInterest, meetsRequiredPreferences } from "../utils/jobDiscovery.js";
import { MatchBreakdown } from "../components/MatchBreakdown.jsx";
import { ExternalApplicationDialog } from "../components/ExternalApplicationDialog.jsx";
import { externalPortal } from "../utils/externalPortal.js";
import { pageItems, totalPages } from "../utils/pagination.js";

export function RecommendationsPage() {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const interests = useJobInterests(true, () => load(false));
  const [query, setQuery] = useState("");
  const [rankingMode, setRankingMode] = useState("balanced");
  const [respectPreferences, setRespectPreferences] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [externalJob, setExternalJob] = useState(null);
  const [sourceFilter, setSourceFilter] = useState(() => readRecommendationSettings(localStorage, user.id).source);
  const [minCompatibility, setMinCompatibility] = useState(() => readRecommendationSettings(localStorage, user.id).minimum);

  const [expandedReasons, setExpandedReasons] = useState({});
  const [page, setPage] = useState(1);
  const pageSize = 5;
  const pendingLoad = useRef(null);

  function load(showLoading = true) {
    // React development effects and simultaneous filter updates can share a
    // request; do not start duplicate expensive calculations for this screen.
    if (pendingLoad.current) return pendingLoad.current;
    pendingLoad.current = fetchRecommendations(showLoading).finally(() => { pendingLoad.current = null; });
    return pendingLoad.current;
  }
  async function fetchRecommendations(showLoading) {
    if (showLoading) setLoading(true);
    setError("");
    try {
      const [
        recommendationsResponse,
        applicationsResponse,
        jobsResponse,
        preferencesResponse,
      ] = await Promise.all([
        getRecommendations(user.id),
        api.get("/applications/me"),
        api.get("/jobs"),
        api.get("/matching/preferences"),
      ]);
      setRecommendations(recommendationsResponse.data);
      setApplications(applicationsResponse.data);
      setJobs(jobsResponse.data);
      setPreferences(preferencesResponse.data);
    } catch {
      setError("No pudimos cargar las recomendaciones. Puedes volver a intentarlo.");
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
  const filteredRecommendations = useMemo(
    () =>
      orderRecommendations(enriched, rankingMode).filter((item) => {
        const job = jobsById.get(item.job_id);
        return job && meetsRequiredPreferences(item, respectPreferences) && searchJob(job, query) && visibleInterest(job, interests.byId, "all") && (sourceFilter === "all" || job.source_kind === sourceFilter);
      }),
    [enriched, jobsById, sourceFilter, query, interests.byId, respectPreferences, rankingMode],
  );
  const pages = totalPages(filteredRecommendations, pageSize);
  const visibleRecommendations = pageItems(filteredRecommendations, page, pageSize);

  useEffect(() => {
    setPage((current) => Math.min(current, pages));
  }, [pages]);

  function changeMinimum(value) {
    const next = Number(value);
    setMinCompatibility(next);
    setPage(1);
    saveRecommendationSetting(localStorage, user.id, "minimum", next);
  }

  function changeSource(value) {
    setSourceFilter(value);
    setPage(1);
    saveRecommendationSetting(localStorage, user.id, "source", value);
  }

  const appliedJobIds = useMemo(
    () => new Set(applications.map((application) => application.job_id)),
    [applications],
  );

  async function apply(job) {
    setMessage("");
    setError("");
    if (job?.source_kind === "external" && job.external_url) {
      setExternalJob(job);
      return;
    }
    try {
      await api.post("/applications", { job_id: job.id });
      setMessage("Postulación registrada correctamente");
      const { data } = await api.get("/applications/me");
      setApplications(data);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "No fue posible registrar la postulación",
      );
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Recomendaciones"
        title="Empleos sugeridos para tu perfil"
        description="Cada vacante muestra compatibilidad, habilidades coincidentes y una guía para mejorar."
      />

      <RecommendationControls interests={interests} jobs={jobs} onSaved={() => { setPage(1); return load(false); }} respectPreferences={respectPreferences} onRespectChange={(value) => { setRespectPreferences(value); setPage(1); }} excludedCount={enriched.filter((item) => !meetsRequiredPreferences(item)).length} />
      <SearchPreferences data={preferences} onSaved={() => load(false)} />
      <label className="block"><span className="sr-only">Buscar recomendaciones</span><input className="field-control" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Buscar por cargo, empresa, ciudad o habilidad" /></label>
      {error && (
        <p className="rounded-[var(--radius-lg)] border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-sm text-[var(--error)]">
          {error} <button type="button" className="ml-3 underline" onClick={() => load()}>Reintentar</button>
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
        <section className="recommendation-results">
          <div className="recommendation-list-heading">
            <div className="recommendation-list-topline">
            <div className="flex items-center gap-3">
              <BriefcaseBusiness className="text-[var(--success)]" size={20} />
              <div>
                <h2 className="font-semibold text-[var(--ink)]">
                  Lista de empleo recomendada
                </h2>
                <p className="text-sm text-[var(--muted)]">
                  {rankingMode === "balanced" ? "Afinidad con tu perfil, información de la oferta y tus preferencias." : "De mayor a menor porcentaje de compatibilidad."}
                </p>
              </div>
            </div>
            <p className="recommendation-count" role="status" aria-live="polite"><strong>{filteredRecommendations.length}</strong><span>{filteredRecommendations.length === 1 ? "oferta recomendada" : "ofertas recomendadas"}<small>Con tus filtros actuales</small></span></p>
            </div>
            <div className="recommendation-filterbar">
              <label className="filter-field">Ordenar<select className="field-control" aria-label="Ordenar recomendaciones" value={rankingMode} onChange={(event) => { setRankingMode(event.target.value); setPage(1); }}><option value="balanced">Recomendadas</option><option value="compatibility">Mayor compatibilidad</option></select></label>
              <label className="filter-field">
                Origen
                <select className="field-control" value={sourceFilter} onChange={(event) => changeSource(event.target.value)}>
                  <option value="all">Todas</option>
                  <option value="internal">TalentSync</option>
                  <option value="external">Externas</option>
                </select>
              </label>
              <label className="filter-field">
                Compatibilidad mínima
                <select className="field-control" value={minCompatibility} onChange={(event) => changeMinimum(event.target.value)}>
                  {[0, 40, 50, 60, 70, 80, 90].map((value) => <option key={value} value={value}>{value}%</option>)}
                </select>
              </label>
            </div>
          </div>

          <div className="recommendation-cards">
            {visibleRecommendations.map((item) => {
              const job = jobsById.get(item.job_id);
              const applied = appliedJobIds.has(item.job_id);
              const isExpanded = expandedReasons[item.id] ?? false;

              const reasonsShort = (item.reasons ?? []).slice(0, 2);


              const categoryLabel =
                item.category === "alta"
                  ? "Alta compatibilidad"
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
                  className="recommendation-card"
                >
                  <div className="recommendation-card-copy">
                    <p className="recommendation-card-company"><Building2 size={14} />{job?.company_name || "Empresa"}{job?.location && <span><MapPin size={13} />{job.location}</span>}</p>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-[var(--ink)]"><Link className="recommendation-title-link" to={`/vacantes/${item.job_id}`} state={{ returnTo: "/recomendaciones" }}>
                        {job?.title ?? "Vacante"}
                      </Link></h3>
                      <span
                        className={`rounded-[var(--radius-md)] border px-2 py-1 text-xs font-semibold text-[var(--ink)] ${categoryTone}`}
                      >
                        {categoryLabel}
                      </span>
                      {job?.source_kind === "external" ? (
                        <span className="rounded-full bg-[var(--accent)]/10 px-2.5 py-1 text-xs font-semibold text-[var(--accent)]">
                          Postulación en {externalPortal(job)}
                        </span>
                      ) : null}
                      {item.discovery?.quality_score != null && <span className="recommendation-quality" title={item.discovery.notice}>Claridad de oferta {item.discovery.quality_score}%</span>}
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
                        className="line-clamp-2 text-xs text-[var(--muted)]"
                      >
                        {reasonsShort[0] || "Compara los requisitos con las habilidades de tu perfil."}
                      </p>
                      {(
                        <button
                          type="button"
                          aria-expanded={isExpanded}
                          onClick={() =>
                            setExpandedReasons((prev) => ({
                              ...prev,
                              [item.id]: !isExpanded,
                            }))
                          }
                          className="recommendation-insight-button"
                        >
                          <TrendingUp
                            size={14}
                            className="text-[var(--success)]"
                          />
                          {isExpanded ? "Ocultar detalle" : "Ver compatibilidad y formación"}
                        </button>
                      )}
                    </div>

                    <JobInterestButtons job={job} interests={interests} />
                    <div className="mt-3">
                      <Link
                        to={`/vacantes/${item.job_id}`}
                        state={{ returnTo: "/recomendaciones" }}
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

                  <CompatibilityBar
                    value={item.match_percentage}
                    estimated={job?.source_kind === "external"}
                    confidence={item.data_confidence_percentage}
                  />

                  <div className="recommendation-card-apply">
                    <button
                      type="button"
                      disabled={applied}
                      onClick={() => apply(job)}
                      className="button-success"
                    >
                      <Send size={16}  />
                      {applied ? "Enviada" : "Postularme"}
                    </button>
                  </div>
                  {isExpanded ? (
                    <div className="recommendation-card-details grid gap-6 border-t border-[var(--line)] pt-5 lg:grid-cols-2">
                      <p className="lg:col-span-2 text-xs text-[var(--muted)]">{item.discovery?.notice}</p>
                      <MatchBreakdown
                        details={item.match_details}
                        skillMatch={item.skill_match_percentage}
                        semanticMatch={item.professional_context_percentage ?? item.semantic_match_percentage}
                        languageMatch={item.language_match_percentage}
                      />
                      <div className="skill-evidence-panel"><SkillRadarChart requirements={item.match_details?.requirements || []} matchPercentage={item.match_percentage} /><RequirementSupport details={item.match_details} /><Link className="mt-4 inline-block text-xs text-[var(--accent)]" to="/perfil#evidencias">Gestionar mis evidencias →</Link></div>

                      <div className="lg:col-span-2"><VacancyLearningPanel jobId={item.job_id} /></div>
                    </div>
                  ) : null}
                </article>
              );
            })}

            {filteredRecommendations.length === 0 ? (
              <div className="px-5 py-10 text-center text-[var(--muted)]">
                <Sparkles
                  size={20}
                  className="mx-auto mb-3 text-[var(--accent)]"
                />
                No hay recomendaciones con estos filtros. Puedes cambiar la
                búsqueda, cambiar el
                origen o reducir el mínimo de {minCompatibility}%.
              </div>
            ) : null}
          </div>
          {filteredRecommendations.length > pageSize ? (
            <nav className="flex flex-col gap-3 border-t border-[var(--line)] px-5 py-4 sm:flex-row sm:items-center sm:justify-between" aria-label="Paginación de recomendaciones">
              <p className="text-sm text-[var(--muted)]">
                Mostrando {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, filteredRecommendations.length)} de {filteredRecommendations.length}
              </p>
              <div className="flex items-center gap-2">
                <button type="button" className="button-secondary button-sm" disabled={page === 1} onClick={() => setPage((current) => current - 1)}><ChevronLeft size={15} />Anterior</button>
                <strong className="px-2 text-sm">{page} / {pages}</strong>
                <button type="button" className="button-secondary button-sm" disabled={page === pages} onClick={() => setPage((current) => current + 1)}>Siguiente<ChevronRight size={15} /></button>
              </div>
            </nav>
          ) : null}
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
      <ExternalApplicationDialog
        job={externalJob}
        onClose={() => setExternalJob(null)}
      />
    </div>
  );
}
