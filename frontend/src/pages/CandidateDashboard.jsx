import { DashboardLearning } from "../components/DashboardLearning.jsx";
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BriefcaseBusiness, CalendarDays, Check, FileUser, MapPin, RotateCcw, Send, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import { useRecommendationUpdates } from "../hooks/useRecommendationUpdates.js";
import { useRecommendations } from "../hooks/useRecommendations.js";
import { readRecommendationSettings } from "../utils/recommendationSettings.js";
import { candidateOpportunities, processOverview, applicationLabels, dashboardDate } from "../utils/dashboardData.js";
import { api, getApiErrorMessage } from "../api/client.js";
import { getRecommendations } from "../api/recommendations.js";
import { getProfileCompletion } from "../components/ProfileCompletionRing.jsx";
import { DashboardAgenda, DashboardEmpty, DashboardSection, DashboardStat } from "../components/DashboardElements.jsx";
import { ExternalApplicationDialog } from "../components/ExternalApplicationDialog.jsx";
import { RequirementSupport } from "../components/RequirementSupport.jsx";
import "../styles/dashboards.css";

const completionTargets = { "Título profesional": "profile-profession", "Teléfono, ciudad y departamento": "profile-contact", "6 habilidades específicas": "profile-skills", "Resumen profesional de 120 caracteres": "profile-summary", "2 experiencias completas": "profile-experiences", "Formación académica completa": "profile-educations", "Curso o certificación": "profile-certifications", "Idioma con nivel": "profile-languages", "Preferencias laborales completas": "preferencias" };
export function CandidateDashboard() {
  const { user } = useAuth(), navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]), [applications, setApplications] = useState([]), [jobs, setJobs] = useState([]), [profile, setProfile] = useState(null);
  const [learningPlans, setLearningPlans] = useState([]);
  const [loading, setLoading] = useState(true), [loadError, setLoadError] = useState(""), [cardFeedback, setCardFeedback] = useState({}), [lastSent, setLastSent] = useState(null), [externalJob, setExternalJob] = useState(null);
  const [minimum] = useState(() => readRecommendationSettings(localStorage, user.id).minimum);
  const { refreshing, error: matchError, retry: retryMatches } = useRecommendationUpdates(user.id, setRecommendations);
  async function load() {
    setLoading(true); setLoadError("");
    const responses = await Promise.allSettled([getRecommendations(user.id).then(({ data }) => setRecommendations(data)), api.get("/applications/me").then(({ data }) => setApplications(data)), api.get("/jobs").then(({ data }) => setJobs(data)), api.get("/profiles/me").then(({ data }) => setProfile(data)), api.get("/learning/plans").then(({ data }) => setLearningPlans(data))]);
    if (responses.some((row) => row.status === "rejected")) setLoadError("Parte de tu información no pudo cargarse. Puedes reintentar sin perder los datos que ya ves.");
    setLoading(false);
  }
  useEffect(() => { load(); }, []);
  const enriched = useRecommendations(recommendations, minimum, false);
  const opportunities = useMemo(() => candidateOpportunities(enriched, jobs, applications), [enriched, jobs, applications]);
  const activity = useMemo(() => processOverview(applications), [applications]);
  const jobsById = useMemo(() => new Map(jobs.map((job) => [job.id, job])), [jobs]);
  const completion = getProfileCompletion(profile), nextField = completion.missing[0];
  const profileLink = `/perfil${completionTargets[nextField] ? `#${completionTargets[nextField]}` : ""}`;
  async function apply(job) {
    if (job.source_kind === "external" && job.external_url) { setExternalJob(job); return; }
    if (job.application_questions?.length || job.application_questions_count) { navigate(`/vacantes/${job.id}#postularme`); return; }
    setCardFeedback((current) => ({ ...current, [job.id]: { busy: true } }));
    try {
      const { data } = await api.post("/applications", { job_id: job.id }, { __quiet: true });
      setApplications((current) => [...current.filter((row) => row.job_id !== data.job_id), data]);
      setLastSent({ id: data.id, title: job.title });
      setCardFeedback((current) => ({ ...current, [job.id]: {} }));
    } catch (error) { setCardFeedback((current) => ({ ...current, [job.id]: { error: getApiErrorMessage(error, "No pudimos registrar la postulación. Vuelve a intentarlo.") } })); }
  }
  return <main className="dashboard-home candidate-home" aria-busy={loading}>
    <header className="dashboard-welcome"><div><span className="dashboard-eyebrow">TU ESPACIO PROFESIONAL</span><h1>Hola, {user.name?.trim().split(/\s+/)[0] || "bienvenido"}</h1><p>{activity.interviews.length ? "Tienes entrevistas próximas. Revisa tu agenda y los detalles de cada proceso." : opportunities.length ? "Hay oportunidades para explorar y procesos que puedes seguir desde aquí." : "Este es el punto de partida para organizar tu búsqueda de empleo."}</p><div className="dashboard-welcome-actions"><Link to="/recomendaciones" className="button-primary"><Sparkles size={17} />Explorar recomendaciones</Link><Link to="/perfil" className="button-secondary"><FileUser size={17} />Mi perfil</Link></div></div><aside className="dashboard-focus"><span>{activity.interviews.length ? "PRÓXIMA ENTREVISTA" : "TU SIGUIENTE PASO"}</span><strong>{activity.interviews.length ? dashboardDate(activity.interviews[0].interview_at) : profile && completion.percentage < 100 ? "Completa lo que falta" : "Elige una oportunidad"}</strong><p>{activity.interviews.length ? activity.interviews[0].job_title || jobsById.get(activity.interviews[0].job_id)?.title : profile && completion.percentage < 100 ? nextField : "Revisa las funciones y los requisitos de la oferta antes de postularte."}</p><Link to={activity.interviews.length ? `/procesos/${activity.interviews[0].id}` : completion.percentage < 100 ? profileLink : "/recomendaciones"}>Abrir detalle<ArrowRight size={15} /></Link></aside></header>
    {(loadError || matchError) && <div className="dashboard-load-note" role="alert"><p>{loadError || matchError}</p><button type="button" onClick={loadError ? load : retryMatches}><RotateCcw size={16} />Reintentar</button></div>}
    <div className="dashboard-stat-grid"><DashboardStat icon={Sparkles} label="Para explorar" value={loading ? "—" : opportunities.length} detail={`Sin postular · desde ${minimum}% de afinidad`} to="/recomendaciones" /><DashboardStat icon={BriefcaseBusiness} label="Procesos activos" value={loading ? "—" : activity.active.length} detail="Postulaciones en seguimiento" to="/postulaciones" /><DashboardStat icon={CalendarDays} label="Entrevistas próximas" value={loading ? "—" : activity.interviews.length} detail="Con fecha registrada" to="/postulaciones" tone="success" /><DashboardStat icon={FileUser} label="Información de tu perfil" value={profile ? `${completion.percentage}%` : "—"} detail="Completitud, no compatibilidad" to="/perfil" /></div>
    {refreshing && <p className="dashboard-refresh-status" role="status"><RotateCcw size={14} />Actualizando compatibilidades. Puedes seguir usando tu espacio.</p>}
    <div className="dashboard-main-grid"><div className="dashboard-main-column"><DashboardSection title="Oportunidades para dar el siguiente paso" subtitle="Las de mayor afinidad que todavía no has solicitado." to="/recomendaciones" action="Ver todas">
      {lastSent && <div className="dashboard-local-success" role="status"><Check size={18} /><span>Postulación enviada: {lastSent.title}</span><Link to={`/procesos/${lastSent.id}`}>Ver proceso<ArrowRight size={14} /></Link></div>}
      <div className="dashboard-job-list">{opportunities.slice(0, 3).map((row) => { const job = jobsById.get(row.job_id), feedback = cardFeedback[job.id] || {}; return <article key={row.id} className="dashboard-job-card"><div className="dashboard-job-heading"><span className="dashboard-job-icon"><BriefcaseBusiness size={21} /></span><div><small>{job.company_name || "Empresa"}</small><h3><Link to={`/vacantes/${job.id}`}>{job.title}</Link></h3></div><div className="dashboard-match-number"><strong>{Math.round(row.match_percentage)}%</strong><small>{job.source_kind === "external" ? "Afinidad estimada" : "Compatibilidad"}</small></div></div><div className="dashboard-job-meta"><span><MapPin size={14} />{job.location || (job.modality === "remote" ? "Remoto" : "Ubicación por confirmar")}</span><span>{({ remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" })[job.modality] || ""}</span></div><p className="dashboard-job-reason">{row.reasons?.[0] || "Consulta los requisitos para conocer el detalle de la comparación."}</p><footer><RequirementSupport details={row.match_details} /><div><Link className="button-secondary button-sm" to={`/vacantes/${job.id}`}>Ver oferta</Link><button type="button" className="button-primary button-sm" disabled={feedback.busy} onClick={() => apply(job)}><Send size={15} />{feedback.busy ? "Enviando…" : job.source_kind === "external" ? "Ver postulación" : "Postularme"}</button></div></footer>{feedback.error && <p className="dashboard-local-error" role="alert">{feedback.error}</p>}</article>; })}</div>{!loading && !opportunities.length && <DashboardEmpty title={enriched.length ? "Ya exploraste estas recomendaciones" : "Aún no hay recomendaciones con este mínimo"} description="Puedes ampliar la búsqueda o revisar los requisitos de otras ofertas disponibles." to="/vacantes" action="Buscar vacantes" />}{loading && !opportunities.length && <p className="dashboard-loading" role="status">Cargando tus oportunidades…</p>}
    </DashboardSection><DashboardSection title="Tus procesos recientes" subtitle="Consulta avances, respuestas y detalles de cada postulación." to="/postulaciones"><div className="dashboard-process-list">{activity.recent.slice(0, 4).map((row) => <Link key={row.id} to={`/procesos/${row.id}`}><span className={`dashboard-process-dot ${row.status}`} /><div><strong>{row.job_title || jobsById.get(row.job_id)?.title || "Vacante"}</strong><small>{row.company_name || ""} · {dashboardDate(row.created_at, false)}</small></div><span className="dashboard-state">{applicationLabels[row.status] || "En seguimiento"}</span><ArrowRight size={15} /></Link>)}</div>{!loading && !activity.recent.length && <DashboardEmpty title="Tu primer proceso aparecerá aquí" description="Al postularte podrás seguir sus etapas y consultar las respuestas de la empresa." />}</DashboardSection></div>
    <aside className="dashboard-side-column"><DashboardSection title="Tu agenda" subtitle="Entrevistas de procesos que siguen activos."><DashboardAgenda items={activity.interviews.slice(0, 3)} jobsById={jobsById} />{!activity.interviews.length && <DashboardEmpty title="Sin entrevistas próximas" description="Cuando una empresa programe una entrevista, tendrás aquí su fecha y el acceso al proceso." />}</DashboardSection><DashboardSection title={completion.percentage === 100 ? "Mantén tu perfil al día" : "Un avance para tu perfil"}><div className="dashboard-profile-progress"><strong>{profile ? `${completion.percentage}%` : "—"}</strong><div><span>{completion.percentage === 100 ? "Los diez apartados tienen información" : nextField || "Cargando tu perfil"}</span><p>{completion.percentage === 100 ? "Actualiza tu experiencia, enlaces y documentos cuando cambien." : "Completa datos reales para que las comparaciones tengan más contexto."}</p></div></div><Link className="dashboard-text-link" to={completion.percentage === 100 ? "/perfil" : profileLink}>Revisar mi perfil<ArrowRight size={15} /></Link></DashboardSection><DashboardLearning plans={learningPlans} certifications={profile?.certifications || []} /></aside></div>
    <ExternalApplicationDialog job={externalJob} onClose={() => setExternalJob(null)} />
  </main>;
}
