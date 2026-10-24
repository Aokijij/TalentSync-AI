import { ChallengeWorkspace, ChallengeResult } from "../components/ChallengeWorkspace.jsx";
import { practiceSeconds, practiceDraft, restorePractice, savePractice } from "../utils/practiceSession.js";
import { ChallengeCatalog } from "../components/ChallengeCatalog.jsx";
import { LearningAreaPicker } from "../components/LearningAreaPicker.jsx";
import { LearningResults } from "../components/LearningResults.jsx";
import { Target, BookOpen, Route, BadgeCheck, TrendingUp } from "lucide-react";
import { MarketRadar } from "../components/MarketRadar.jsx";
import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { LearningResourceCard } from "../components/LearningResourceCard.jsx";
import { LearningOverview } from "../components/LearningVisuals.jsx";
import { LearningPlanBoard } from "../components/LearningPlanBoard.jsx";
import { activityComplete } from "../components/ActivityInput.jsx";
import { LearningFilters } from "../components/LearningFilters.jsx";
import { LearningOpportunities } from "../components/PublicLearningSources.jsx";
import { filterResources } from "../utils/learningFilters.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { Pagination } from "../components/Pagination.jsx";

export function LearningPage() {
  const { user } = useAuth();
  const { confirm, notify } = useFeedback();
  const location = useLocation();
  const [filters, setFilters] = useState(() => ({ query: new URLSearchParams(location.search).get("search") || "" }));
  const challengeFocus = new URLSearchParams(location.search).get("challenge");
  const [planSelection, setPlanSelection] = useState(new URLSearchParams(location.search).get("resource") || null);
  const [coursePage, setCoursePage] = useState(1);
  function chooseArea(next) { setArea(next); setFilters({}); setCoursePage(1); }
  const returnToChallenge = useRef(null);
  const practiceMemory = useRef({});
  const [practiceOpen, setPracticeOpen] = useState(false), [draftWarning, setDraftWarning] = useState("");
  const [area, setArea] = useState(new URLSearchParams(location.search).has("search") || challengeFocus ? "all" : "recommended"), [tab, setTab] = useState(["#que-aprender", "#radar-laboral"].includes(location.hash) ? "demand" : location.hash === "#mi-plan" ? "plan" : location.hash === "#resultados" ? "passport" : location.hash === "#cursos" ? "courses" : ["#retos", "#retos-sql"].includes(location.hash) ? "challenges" : "courses");
  useEffect(() => { const search = new URLSearchParams(location.search).get("search"); if (search) { setFilters({ query: search }); setArea("all"); setTab("courses"); setCoursePage(1); } }, [location.search]);
  useEffect(() => { if (challengeFocus) { setArea("all"); setTab("challenges"); } const resource = new URLSearchParams(location.search).get("resource"); if (resource) setPlanSelection(resource); }, [challengeFocus, location.search]);
  const [catalogResult, setCatalogResult] = useState(null), [plans, setPlans] = useState([]), [passport, setPassport] = useState(null);
  const [catalogError, setCatalogError] = useState(""), [catalogLoading, setCatalogLoading] = useState(true), [reload, setReload] = useState(0);
  const [attempt, setAttempt] = useState(null), [answers, setAnswers] = useState({}), [step, setStep] = useState(0);
  const [error, setError] = useState(""), [busy, setBusy] = useState(false), [now, setNow] = useState(Date.now());
  async function refresh() { const results = await Promise.allSettled([api.get("/learning/plans").then(({ data }) => setPlans(data)), api.get("/learning/passport").then(({ data }) => setPassport(data))]); const failed = results.find((row) => row.status === "rejected" && row.reason.code !== "ERR_CANCELED"); setError(failed ? getApiErrorMessage(failed.reason, "No pudimos actualizar tu plan o tus resultados. Vuelve a intentarlo.") : ""); }
  useEffect(() => { refresh(); }, []);
  useEffect(() => { const controller = new AbortController(); setCatalogLoading(true); setCatalogError(""); api.get("/learning/catalog", { params: { area }, signal: controller.signal, __skipRetry: true }).then(({ data }) => { if (!controller.signal.aborted) setCatalogResult({ area, data }); }).catch((failure) => { if (!controller.signal.aborted) setCatalogError(getApiErrorMessage(failure, "No pudimos cargar los retos y cursos de esta área.")); }).finally(() => { if (!controller.signal.aborted) setCatalogLoading(false); }); return () => controller.abort(); }, [area, reload]);
  useEffect(() => { if (attempt?.status !== "active") return; const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, [attempt]);
  useEffect(() => {
    if (practiceOpen || tab !== "challenges" || !returnToChallenge.current) return;
    const assessmentId = returnToChallenge.current;
    const frame = requestAnimationFrame(() => { document.getElementById(`challenge-start-${assessmentId}`)?.focus(); returnToChallenge.current = null; });
    return () => cancelAnimationFrame(frame);
  }, [practiceOpen, tab]);
  useEffect(() => {
    if (!draftWarning || attempt?.status !== "active") return;
    const warn = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [draftWarning, attempt?.status]);
  useEffect(() => { if (["#que-aprender", "#radar-laboral", "#mi-plan", "#resultados", "#cursos", "#retos", "#retos-sql"].includes(location.hash)) { setTab({ "#radar-laboral": "demand", "#que-aprender": "demand", "#mi-plan": "plan", "#resultados": "passport", "#cursos": "courses", "#retos": "challenges", "#retos-sql": "challenges" }[location.hash]); } }, [location.hash]);
  async function addPlan(id) { const { data } = await api.put(`/learning/plans/${id}`, { status: "in_progress" }, { __quiet: true }); setPlans(data); const resource = data.find((row) => row.resource?.id === id)?.resource; notify(resource?.url ? "El curso se ha guardado para seguir tu formación." : "La práctica está lista para comenzar.", { title: "Añadido a Mi plan", action: { label: "Abrir Mi plan", onClick: () => { setPracticeOpen(false); setPlanSelection(id); setTab("plan"); } } }); return true; }
  async function act(action) { setBusy(true); setError(""); try { return await action(); } catch (failure) { setError(getApiErrorMessage(failure)); return false; } finally { setBusy(false); } }
  const draftKey = (id) => `talentsync-assessment-${user.id}-${id}`;
  const draftStorage = { getItem: (key) => window.sessionStorage.getItem(key), setItem: (key, value) => window.sessionStorage.setItem(key, value) };
  async function start(id) {
    const { data } = await api.post(`/learning/assessments/${id}/start`, null, { __quiet: true });
    if (!Array.isArray(data.questions) || !data.questions.length) throw new Error("La práctica no tiene preguntas disponibles.");
    const restored = restorePractice(draftStorage, draftKey(data.id), data.questions);
    const memory = practiceDraft(practiceMemory.current[data.id], data.questions);
    const recovered = { ...restored.answers, ...memory };
    const next = data.questions.findIndex((item) => !activityComplete(item, recovered[item.id]));
    practiceMemory.current[data.id] = recovered;
    returnToChallenge.current = id;
    setAttempt(data); setAnswers(recovered); setStep(next < 0 ? data.questions.length : next);
    setDraftWarning(restored.warning); setPracticeOpen(true); setNow(Date.now());
  }
  function choose(id, value) {
    const next = { ...answers, [id]: value };
    practiceMemory.current[attempt.id] = next;
    setAnswers(next); setDraftWarning(savePractice(draftStorage, draftKey(attempt.id), next));
  }
  const seconds = attempt ? practiceSeconds(attempt.expires_at, now) : 0;
  function openResult(row) { returnToChallenge.current = row.assessment_id; setAttempt(row); setError(""); setPracticeOpen(true); }
  function exitPractice(destination = "challenges") { setPracticeOpen(false); setTab(destination); setError(""); setReload((value) => value + 1); }
  async function submitPractice() {
    if (busy || seconds === 0) return;
    if (!await confirm({ title: "Entregar la práctica", description: "Se evaluarán tus respuestas y verás las correcciones. La entrega finaliza este intento.", confirmLabel: "Entregar respuestas" })) return;
    await act(async () => {
      const { data } = await api.post(`/learning/attempts/${attempt.id}/submit`, { answers }, { __quiet: true });
      setAttempt(data); setDraftWarning("");
      delete practiceMemory.current[attempt.id];
      try { window.sessionStorage.removeItem(draftKey(attempt.id)); } catch { /* The submitted result takes precedence over local cleanup. */ }
      await refresh(); setReload((value) => value + 1);
    });
  }
  const catalog = catalogResult?.area === area && !catalogLoading && !catalogError ? catalogResult.data : null;
  const visibleResources = catalog ? filterResources(catalog.resources.filter((resource) => !plans.some((plan) => plan.resource?.id === resource.id)), filters) : [];
  const coursePages = Math.max(1, Math.ceil(visibleResources.length / 12)), safeCoursePage = Math.min(coursePage, coursePages);
  if (practiceOpen && attempt?.status === "active") return <ChallengeWorkspace attempt={attempt} answers={answers} step={step} onStep={setStep} onAnswer={choose} seconds={seconds} busy={busy} error={error} warning={draftWarning} onExit={() => exitPractice()} onSubmit={submitPractice} />;
  if (practiceOpen && attempt?.status === "completed") return <ChallengeResult attempt={attempt} error={error} onExit={() => exitPractice()} onResults={() => exitPractice("passport")}>
    {!!attempt.improvement_resources?.length && <section className="space-y-3"><h2 className="text-lg font-bold">Formación para reforzar esta habilidad</h2><div className="grid gap-3 md:grid-cols-2">{attempt.improvement_resources.map((resource) => <LearningResourceCard key={resource.id} resource={resource} busy={busy || plans.filter((row) => row.status !== "completed").length >= 3} inPlan={plans.some((row) => row.resource?.id === resource.id)} onPlan={(id) => act(() => addPlan(id))} />)}</div></section>}
  </ChallengeResult>;
  return <div className="space-y-5">
    <PageHeader kicker="Mi desarrollo" title="Aprende y demuestra lo que sabes" description="Continúa tu formación desde Mi plan, explora cursos o practica una habilidad para encontrar qué necesitas reforzar." />
    <LearningOverview plans={plans} passport={passport} />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error} <button className="underline" onClick={refresh}>Reintentar</button></p>}
    <nav aria-label="Secciones de desarrollo" className="learning-navigation">{[["challenges", "Retos", Target], ["courses", "Cursos y prácticas", BookOpen], ["demand", "Radar laboral", TrendingUp], ["plan", "Mi plan", Route], ["passport", "Mis resultados", BadgeCheck]].map(([key, label, Icon]) => <button aria-pressed={tab === key} key={key} onClick={() => { setTab(key); }}><Icon size={19} /><span>{label}</span>{key === "plan" && <small>{plans.length}</small>}</button>)}</nav>
    {tab === "demand" && <section className="space-y-4"><MarketRadar /></section>}
    {["challenges", "courses"].includes(tab) && <LearningAreaPicker areas={catalogResult?.data?.areas} value={area} onChange={chooseArea} />}
    {["challenges", "courses"].includes(tab) && catalogLoading && <p role="status" className="surface-card p-4">Cargando retos y cursos…</p>}
    {["challenges", "courses"].includes(tab) && catalogError && <p role="alert" className="surface-card p-4 text-[var(--error)]">{catalogError} <button className="underline" onClick={() => setReload((value) => value + 1)}>Reintentar</button></p>}
    {tab === "challenges" && catalog && <ChallengeCatalog focusId={challengeFocus} plans={plans} sources={catalog.challenge_sources} demandNote={catalog.challenge_demand_note} assessments={catalog.assessments} areas={catalog.areas} busy={busy} attempt={attempt} onStart={(id) => act(() => start(id))} onReview={(id) => { const result = passport?.assessments.find((row) => row.id === id); if (result) { openResult(result); } else { setTab("passport"); } }} onExplore={(skill) => { setFilters({ query: skill }); setArea("all"); setCoursePage(1); setTab("courses"); }} />}
    {tab === "courses" && catalog && <section className="space-y-4"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-bold">Cursos y prácticas para avanzar</h2></div><LearningFilters value={filters} resultCount={visibleResources.length} resources={catalog.resources} onChange={(next) => { setFilters(next); setCoursePage(1); }} /><p className="text-xs text-[var(--muted)]">El acceso gratuito al curso puede tener condiciones distintas al certificado. Consulta los detalles y la página oficial antes de inscribirte.</p><p className="text-sm text-[var(--muted)]">{plans.filter((row) => row.status !== "completed").length}/3 recursos activos{plans.filter((row) => row.status !== "completed").length >= 3 ? " · Finaliza o abandona uno para añadir otro." : " · Puedes añadir formación a Mi plan."}</p><div className="learning-catalog-grid">{visibleResources.slice((safeCoursePage - 1) * 12, safeCoursePage * 12).map((resource) => <LearningResourceCard key={resource.id} resource={resource} busy={busy || plans.filter((row) => row.status !== "completed").length >= 3} onPlan={(id) => act(() => addPlan(id))} />)}</div><Pagination page={safeCoursePage} pages={coursePages} total={visibleResources.length} pageSize={12} onChange={setCoursePage} label="Páginas de cursos y prácticas" />{visibleResources.length === 0 && <p role="status" className="learning-empty">No hay recursos con estos filtros. Cambia el origen, el coste o el área para explorar otras opciones.</p>}{catalog.resources.length > 0 && catalog.resources.every((resource) => plans.some((plan) => plan.resource?.id === resource.id)) && <div className="learning-empty"><h3 className="font-bold">Ya tienes estos recursos en tu plan</h3><button className="button-primary" onClick={() => setTab("plan")}>Continuar en Mi plan →</button></div>}</section>}
    {tab === "courses" && <LearningOpportunities />}
    {tab === "plan" && <LearningPlanBoard key={planSelection || "plan"} initialResourceId={planSelection} onReturn={() => setPlanSelection(null)} plans={plans} onSaved={async (data, published) => { setPlans(data); if (published) await refresh(); }} onReload={refresh} onExplore={() => setTab("courses")} />}
    {tab === "passport" && passport && <LearningResults plans={plans} onOpenPractice={(resourceId) => { setPlanSelection(resourceId); setTab("plan"); }} onReload={refresh} passport={passport} onReview={openResult} />}
  </div>;
}
