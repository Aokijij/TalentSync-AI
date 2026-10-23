import { useEffect, useRef, useState } from "react";
import { Archive, ArrowDownUp, ArrowRight, BriefcaseBusiness, CalendarClock, Check, Columns3, Inbox, List, RefreshCw, Search, Settings2, Sparkles } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../../api/client.js";
import { useFeedback } from "../../contexts/FeedbackContext.jsx";
import { PageHeader } from "../PageHeader.jsx";
import { WorkspaceTabs } from "../ui/Panel.jsx";
import { Pagination } from "../Pagination.jsx";
import { ApplicationAnswersModal } from "../ApplicationAnswersModal.jsx";
import { RecruiterProcessDialog } from "../RecruiterProcessDialog.jsx";
import { ReopenJobModal } from "../ReopenJobModal.jsx";
import { applicationBaseMatch, mergeApplicationMatch } from "../../utils/applicationMatch.js";
import { interviewDateParts } from "../../utils/interviewAgenda.js";
import { ApplicantDetail, ApplicantScore } from "./ApplicantDetail.jsx";
import { ActivePipeline } from "./ActivePipeline.jsx";
import { JobPickerModal, StageEditorModal } from "./RecruitmentDialogs.jsx";
import { RecruitmentDecisionDialog } from "./RecruitmentDecisionDialog.jsx";
import "../../styles/recruitment-workspace.css";

const defaults = [{ id: "submitted", title: "Recibidas" }, { id: "reviewing", title: "En revisión" }, { id: "interview", title: "Entrevista" }, { id: "hired", title: "Contratados" }, { id: "rejected", title: "No seleccionados" }];
const finalIds = new Set(["hired", "accepted", "rejected"]);
const buckets = [["inbox", "Por revisar", Inbox], ["active", "Proceso activo", Columns3], ["interviews", "Entrevistas", CalendarClock], ["closed", "Finalizados", Archive]];

export function RecruitmentWorkspace() {
  const [params, setParams] = useSearchParams(), { confirm } = useFeedback();
  const [jobs, setJobs] = useState([]), [jobsRevision, setJobsRevision] = useState(0), [jobId, setJobId] = useState(params.get("job") || "");
  const [bucket, setBucket] = useState(buckets.some(([key]) => key === params.get("section")) ? params.get("section") : "inbox");
  const [presentation, setPresentation] = useState("board"), [query, setQuery] = useState(""), [search, setSearch] = useState("");
  const [scoreFilter, setScoreFilter] = useState("all"), [order, setOrder] = useState("score"), [page, setPage] = useState(1);
  const [result, setResult] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(Number(params.get("focus")) || null), [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false), [detailError, setDetailError] = useState("");
  const [revision, setRevision] = useState(0), [detailRevision, setDetailRevision] = useState(0), [busy, setBusy] = useState(false), [notice, setNotice] = useState("");
  const [picker, setPicker] = useState(false), [stageEditor, setStageEditor] = useState(false), [reopen, setReopen] = useState(false);
  const [manage, setManage] = useState(false), [answers, setAnswers] = useState(false), [reject, setReject] = useState(false), [nextStage, setNextStage] = useState("");
  const versions = useRef(new Map()), list = useRef(null);
  const job = jobs.find((item) => String(item.id) === jobId), stages = job?.pipeline_stages?.length ? job.pipeline_stages : defaults;
  const advanceStages = stages.filter((item, index) => index > 0 && !finalIds.has(item.id));
  const board = bucket === "active" && presentation === "board";
  useEffect(() => { let active = true; setError(""); setLoading(true); api.get("/jobs/mine/board", { __quiet: true }).then(({ data }) => { if (!active) return; setJobs(data); const initial = data.find((item) => String(item.id) === jobId) || data[0]; if (initial) setJobId(String(initial.id)); else setLoading(false); }).catch((failure) => { if (active) { setError(getApiErrorMessage(failure)); setLoading(false); } }); return () => { active = false; }; }, [jobsRevision]);
  useEffect(() => { const timer = setTimeout(() => { setSearch(query); setPage(1); }, 250); return () => clearTimeout(timer); }, [query]);
  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController(); setLoading(true); setError("");
    api.get(`/applications/jobs/${jobId}/workspace`, { params: { bucket, search, score_filter: scoreFilter, order, page, page_size: board ? 1 : 25 }, signal: controller.signal, __quiet: true }).then(({ data }) => { if (controller.signal.aborted) return; setResult(data); if (page !== data.page) setPage(data.page); }).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [jobId, bucket, search, scoreFilter, order, page, board, revision]);
  useEffect(() => {
    setDetail(null); setDetailError("");
    if (!selectedId || !jobId) { setDetailLoading(false); return; }
    const controller = new AbortController(); setDetailLoading(true);
    async function load() {
      try {
        const { data } = await api.get(`/applications/${selectedId}/review`, { signal: controller.signal, __quiet: true });
        if (controller.signal.aborted) return;
        if (String(data.application.job_id) !== jobId) throw new Error("La candidatura no pertenece a la vacante seleccionada.");
        versions.current.set(data.application.id, data.application.version);
        setDetail(data);
        const currentIndex = stages.findIndex((item) => item.id === data.application.pipeline_stage);
        setNextStage(advanceStages.find((item) => stages.indexOf(item) > currentIndex)?.id || "");
        if (!data.application.reviewed_at) {
          const reviewed = await api.post(`/applications/${selectedId}/reviewed`, { expected_version: data.application.version }, { signal: controller.signal, __quiet: true });
          if (controller.signal.aborted) return;
          versions.current.set(data.application.id, reviewed.data.version);
          if (!reviewed.data.first_review && reviewed.data.version !== data.application.version) {
            const fresh = await api.get(`/applications/${selectedId}/review`, { signal: controller.signal, __quiet: true });
            if (controller.signal.aborted) return;
            setDetail(fresh.data);
            const freshIndex = stages.findIndex((item) => item.id === fresh.data.application.pipeline_stage);
            setNextStage(advanceStages.find((item) => stages.indexOf(item) > freshIndex)?.id || "");
          } else setDetail({ ...data, application: { ...data.application, ...reviewed.data } });
          setResult((current) => current ? { ...current, unreviewed: Math.max(0, current.unreviewed - (reviewed.data.first_review && bucket === "inbox" ? 1 : 0)), items: current.items.map((item) => item.id === selectedId ? { ...item, ...reviewed.data } : item) } : current);
        }
      } catch (failure) { if (!controller.signal.aborted) setDetailError(getApiErrorMessage(failure, failure.message)); }
      finally { if (!controller.signal.aborted) setDetailLoading(false); }
    }
    void load(); return () => controller.abort();
  }, [selectedId, jobId, detailRevision]);

  useEffect(() => {
    if (selectedId && window.matchMedia("(max-width:760px)").matches) requestAnimationFrame(() => document.querySelector(".recruitment-detail-wrap")?.scrollIntoView({ block: "start", behavior: "smooth" }));
  }, [selectedId]);
  useEffect(() => { list.current?.querySelector(".applicant-list-scroll")?.scrollTo({ top: 0 }); }, [page, search, bucket]);
  function closeDetail() {
    const id = selectedId; setSelectedId(null);
    requestAnimationFrame(() => {
      list.current?.querySelector(`[data-application-id="${id}"]`)?.focus({ preventScroll: true });
      if (window.matchMedia("(max-width:760px)").matches) list.current?.scrollIntoView({ block: "start", behavior: "smooth" });
    });
  }

  function changeSection(value) { if (busy) return; setBucket(value); setPage(1); setResult(null); setSelectedId(null); setScoreFilter("all"); setParams({ job: jobId, section: value }, { replace: true }); }
  function chooseJob(value) { if (busy) return; versions.current.clear(); setJobId(String(value.id)); setPage(1); setResult(null); setSelectedId(null); setPicker(false); setNotice(""); setParams({ job: String(value.id), section: bucket }, { replace: true }); }
  function select(id) { if (!busy) { setSelectedId(id); setNotice(""); } }
  function changeFilter(setter, value) { if (busy) return; setter(value); setPage(1); setSelectedId(null); }
  async function save(changes, { moveNext = false } = {}) {
    if (!detail || busy || detailLoading) throw new Error("Espera a que termine de cargar la candidatura.");
    setBusy(true); setDetailError(""); setNotice("");
    try {
      const { data } = await api.put(`/applications/${detail.application.id}/status`, { ...changes, expected_version: detail.application.version }, { __quiet: true });
      versions.current.set(data.id, data.version);
      setManage(false); setAnswers(false); setReject(false);
      if (moveNext) { const index = result?.items.findIndex((item) => item.id === selectedId) ?? -1; setSelectedId(result?.items[index + 1]?.id || null); }
      else { setDetail((current) => ({ ...current, application: { ...current.application, ...data } })); }
      setRevision((value) => value + 1);
      setNotice(changes.recruiter_notes !== undefined && Object.keys(changes).length === 1 ? "Notas internas guardadas." : "Cambios guardados. Consulta los avances y comunicaciones en el historial.");
    } catch (failure) { setDetailError(getApiErrorMessage(failure)); throw failure; }
    finally { setBusy(false); }
  }
  async function advance() { try { await save({ pipeline_stage: nextStage }, { moveNext: bucket === "inbox" }); } catch { /* The selected profile keeps the failure visible. */ } }
  async function hire() { if (await confirm({ title: "Confirmar contratación", description: `Se comunicará la contratación a ${detail.application.candidate_name}. El cambio quedará en el historial.`, confirmLabel: "Confirmar y notificar" })) { try { await save({ status: "hired" }, { moveNext: true }); } catch { /* Keep the selected candidature. */ } } }
  function shortcuts(event) {
    if (busy || loading || detailLoading || manage || answers || reject || stageEditor || picker || reopen || event.repeat || event.ctrlKey || event.metaKey || event.altKey || event.target.closest("input, textarea, select, [contenteditable=true]")) return;
    const items = result?.items || [], current = items.findIndex((item) => item.id === selectedId);
    if (["ArrowDown", "ArrowUp"].includes(event.key) && !board && items.length) { event.preventDefault(); const next = Math.max(0, Math.min(items.length - 1, current + (event.key === "ArrowDown" ? 1 : -1))); select(items[next].id); list.current?.querySelector(`[data-application-id="${items[next].id}"]`)?.focus(); }
    if (detail && !detail.application.released_at && !["rejected", "accepted", "hired"].includes(detail.application.status)) {
      if (event.key.toLowerCase() === "a" && nextStage) { event.preventDefault(); void advance(); }
      if (event.key.toLowerCase() === "r") { event.preventDefault(); setReject(true); }
    }
  }
  async function moveInBoard(row, stage) {
    if (busy || String(row.job_id) !== jobId) return;
    setBusy(true); setError("");
    try {
      const { data } = await api.put(`/applications/${row.id}/status`, { pipeline_stage: stage, expected_version: Math.max(row.version, versions.current.get(row.id) || 0) }, { __quiet: true });
      versions.current.set(data.id, data.version);
      setRevision((value) => value + 1);
      if (selectedId === row.id) setDetailRevision((value) => value + 1);
      setNotice("Etapa actualizada y comunicada al candidato.");
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function calculate() {
    setBusy(true);
    try {
      const { data } = await api.get(`/recommendations/jobs/${jobId}/candidates/${detail.application.user_id}/explanation`, { __quiet: true });
      if (applicationBaseMatch(data) == null) throw new Error("No se recibió la compatibilidad base.");
      setDetail((current) => ({ ...current, application: mergeApplicationMatch(current.application, data) }));
      setRevision((value) => value + 1);
      return data;
    } catch (failure) { setDetailError(getApiErrorMessage(failure)); throw failure; }
    finally { setBusy(false); }
  }

  async function saveStages(values) { try { const { data } = await api.patch(`/jobs/${jobId}`, { pipeline_stages: values }, { __quiet: true }); setJobs((current) => current.map((item) => item.id === data.id ? { ...item, ...data } : item)); setStageEditor(false); setRevision((value) => value + 1); if (selectedId) setDetailRevision((value) => value + 1); } catch (failure) { setError(getApiErrorMessage(failure)); setStageEditor(false); } }
  async function cover() { if (!await confirm({ title: "Marcar vacante como cubierta", description: "Las candidaturas sin contratar se finalizarán y recibirán el aviso correspondiente. Sus historiales se conservan.", confirmLabel: "Cubrir y notificar" })) return; setBusy(true); try { const { data } = await api.patch(`/jobs/${jobId}`, { status: "filled" }, { __quiet: true }); setJobs((current) => current.map((item) => item.id === data.id ? { ...item, ...data } : item)); setSelectedId(null); setRevision((value) => value + 1); setNotice("Vacante cubierta. Los procesos finalizados conservan su historial."); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }

  return <div className="recruitment-workspace" onKeyDown={shortcuts}>
    <PageHeader kicker="Selección de talento" title="Postulaciones" description="Revisa las nuevas candidaturas y dedica tu proceso activo a quienes avanzan." />
    <section className="recruitment-vacancy surface-card"><span className="recruitment-vacancy-icon"><BriefcaseBusiness size={23} /></span><div><span className="section-kicker">Vacante seleccionada</span><h2>{job?.title || (loading ? "Cargando vacantes…" : "Selecciona una vacante")}</h2><p>{result ? Object.entries(result.counts).filter(([key]) => key !== "interviews").reduce((sum, [, value]) => sum + value, 0) : job?.applications_count ?? "—"} candidaturas · {job?.status === "filled" ? "Vacante cubierta" : "Seguimiento por etapas"}</p></div><button type="button" className="button-secondary" disabled={busy} onClick={() => setPicker(true)}>Cambiar vacante</button>{job && <details className="recruitment-vacancy-menu"><summary aria-label="Opciones de la vacante"><Settings2 size={17} /></summary><div><button type="button" onClick={() => setStageEditor(true)} disabled={busy}>Editar etapas</button><button type="button" disabled={busy || job.status !== "filled" && !(result?.hired_count > 0)} onClick={() => job.status === "filled" ? setReopen(true) : void cover()}>{job.status === "filled" ? "Reabrir vacante" : "Marcar como cubierta"}</button></div></details>}</section>
    {notice && <p role="status" className="recruitment-success"><Check size={17} />{notice}<button className="button-ghost button-sm" onClick={() => setNotice("")}>Cerrar</button></p>}
    {error && <p role="alert" className="recruitment-error">{error}<button type="button" className="button-secondary button-sm" onClick={() => jobs.length ? setRevision((value) => value + 1) : setJobsRevision((value) => value + 1)}>Volver a intentar</button></p>}
    {job && <><WorkspaceTabs id="recruitment" label="Secciones de postulaciones" value={bucket} onChange={changeSection} items={buckets.map(([key, title, Icon]) => [key, `${title}${result ? ` (${result.counts[key]})` : ""}`, Icon])} />
    <section id={`recruitment-panel-${bucket}`} role="tabpanel" aria-labelledby={`recruitment-tab-${bucket}`} className="recruitment-section">
      <div className="recruitment-section-heading"><div><h2>{bucket === "inbox" ? "Tu bandeja de candidaturas" : bucket === "active" ? "Personas que avanzan en el proceso" : bucket === "interviews" ? "Próximas entrevistas de esta vacante" : "Decisiones e historial"}</h2><p>{bucket === "inbox" ? `${result?.unreviewed ?? "—"} sin revisar · La compatibilidad orienta; tú decides quién avanza.` : bucket === "active" ? "Cada etapa contiene únicamente candidaturas activas. Las nuevas se revisan en la bandeja. Mover una tarjeta guarda y comunica el avance." : bucket === "interviews" ? "Abre una candidatura para cambiar fecha, modalidad o acceso. Hora de Colombia." : "Consulta las candidaturas finalizadas y las comunicaciones enviadas."}</p></div>{bucket === "active" && <div className="recruitment-view-switch" role="group" aria-label="Vista del proceso"><button type="button" aria-pressed={presentation === "board"} onClick={() => setPresentation("board")}><Columns3 size={16} />Tablero</button><button type="button" aria-pressed={presentation === "list"} onClick={() => setPresentation("list")}><List size={16} />Lista</button></div>}</div>
      <div className="recruitment-filters"><label className="recruitment-search"><Search size={17} /><input aria-label="Buscar candidatura" placeholder="Nombre o profesión" value={query} maxLength={150} disabled={busy} onChange={(event) => { setQuery(event.target.value); setSelectedId(null); }} /></label><label><Sparkles size={15} /><select aria-label="Filtrar candidaturas" className="field-control" value={scoreFilter} disabled={busy} onChange={(event) => changeFilter(setScoreFilter, event.target.value)}><option value="all">Todas las candidaturas</option>{bucket === "inbox" && <option value="unreviewed">Sin revisar</option>}<option value="strong">Compatibilidad ≥ 85%</option><option value="missing">Sin cálculo disponible</option></select></label><label><ArrowDownUp size={15} /><select aria-label="Ordenar candidaturas" className="field-control" value={order} disabled={busy} onChange={(event) => changeFilter(setOrder, event.target.value)}><option value="score">Mayor compatibilidad</option><option value="oldest">Más antiguas primero</option><option value="recent">Más recientes primero</option></select></label><button type="button" className="button-secondary button-sm" disabled={busy || loading} onClick={() => setRevision((value) => value + 1)} aria-label="Actualizar candidaturas"><RefreshCw size={16} /></button></div>
      <div className={`recruitment-content ${selectedId ? "has-selection" : ""} ${board ? "is-board" : ""}`}>
        <div className="recruitment-candidate-list" ref={list} aria-label="Lista de candidaturas" aria-busy={loading}>
          {board ? <ActivePipeline key={`${jobId}:${search}:${scoreFilter}:${order}:${revision}`} jobId={jobId} stages={stages} counts={result?.stage_counts || {}} search={search} scoreFilter={scoreFilter} order={order} revision={revision} onSelect={select} selectedId={selectedId} onMove={moveInBoard} busy={busy || detailLoading} /> : <>
          <header><strong>{loading ? "Consultando candidaturas…" : error ? "Consulta interrumpida" : `${result?.total ?? 0} resultados`}</strong><small>↑ ↓ Navegar · A Avanzar · R Revisar finalización</small></header>
          <div className="applicant-list-scroll">{loading ? <p className="recruitment-empty-note" role="status">Cargando la página de candidatos…</p> : error ? <p className="recruitment-empty-note">No pudimos cargar las candidaturas. Vuelve a intentar la consulta.</p> : !result?.items.length ? <div className="recruitment-list-empty"><Inbox size={30} /><h3>{bucket === "inbox" && !search && scoreFilter === "all" ? "Tu bandeja está al día" : "Sin resultados con estos filtros"}</h3><p>{bucket === "inbox" ? "Las nuevas postulaciones aparecerán aquí. Quienes avanzan están en Proceso activo." : "Prueba otro filtro o consulta las otras secciones."}</p></div> : result.items.map((row) => <button type="button" data-application-id={row.id} className={`applicant-list-row ${selectedId === row.id ? "is-selected" : ""}`} key={row.id} aria-pressed={selectedId === row.id} onClick={() => select(row.id)}><span className={`applicant-avatar ${row.reviewed_at ? "is-reviewed" : ""}`}>{row.reviewed_at ? <Check size={18} /> : <UserInitial name={row.candidate_name} />}</span><span className="applicant-list-info"><strong>{row.candidate_name}</strong><span>{row.profession || "Perfil por completar"}</span><small>{bucket === "active" ? `${stages.find((item) => item.id === (row.effective_stage || row.pipeline_stage))?.title || "En seguimiento"} · ` : ""}{row.reviewed_at ? "Revisado" : "Sin revisar"} · {new Date(`${row.created_at.replace(/Z$/, "")}Z`).toLocaleDateString("es-CO", { timeZone: "America/Bogota" })}</small>{bucket === "interviews" && <span className="applicant-row-interview">{interviewDateParts(row.interview_at)?.full} · {interviewDateParts(row.interview_at)?.time}<small>{row.interview_details?.mode === "virtual" ? "Virtual" : row.interview_details?.mode === "in_person" ? "Presencial" : "Modalidad por confirmar"}</small></span>}</span><ApplicantScore row={row} /><ArrowRight size={15} className="applicant-row-arrow" /></button>)}</div>
          {!loading && result && <Pagination page={result.page} total={result.total} pageSize={25} busy={busy} label="Páginas de candidaturas" onChange={(value) => { setPage(value); setSelectedId(null); }} />}
          </>}
        </div>
        <div className="recruitment-detail-wrap"><ApplicantDetail key={selectedId || "empty"} data={detail} loading={detailLoading} error={detailError} busy={busy} nextStage={nextStage} onNextStage={setNextStage} stages={advanceStages} onAdvance={advance} onReject={() => setReject(true)} onHire={bucket === "active" ? hire : null} onManage={() => setManage(true)} onAnswers={() => setAnswers(true)} onClose={closeDetail} onRetry={() => setDetailRevision((value) => value + 1)} />{detail?.application.adjusted_match_percentage == null && detail && <button type="button" className="button-secondary recruitment-calculate" disabled={busy || detailLoading} onClick={() => { void calculate().catch(() => {}); }}>Calcular compatibilidad de este perfil</button>}</div>
      </div>
    </section></>}
    {picker && <JobPickerModal jobs={jobs} selectedId={jobId} onSelect={chooseJob} onClose={() => setPicker(false)} />}
    {stageEditor && <StageEditorModal stages={stages} counts={result?.all_stage_counts || {}} onSave={saveStages} onClose={() => setStageEditor(false)} />}
    {manage && detail && <RecruiterProcessDialog application={detail.application} onClose={() => setManage(false)} onSave={(changes) => save(changes)} onRequestFinalize={() => { setManage(false); setReject(true); }} onDelete={async () => { setManage(false); setReject(true); }} />}
    {answers && detail && <ApplicationAnswersModal application={detail.application} onClose={() => setAnswers(false)} loadCompatibility={calculate} onSaved={(data) => { setDetail((current) => ({ ...current, application: data })); setRevision((value) => value + 1); setNotice("Valoración interna guardada."); }} />}
    {reject && detail && <RecruitmentDecisionDialog application={detail.application} onClose={() => setReject(false)} onConfirm={(changes) => save(changes, { moveNext: true })} />}
    {reopen && job && <ReopenJobModal job={job} onClose={() => setReopen(false)} onReopened={(updated, mode) => { setJobs((current) => mode === "continue" ? current.map((item) => item.id === updated.id ? updated : item) : [...current, updated]); setReopen(false); chooseJob(updated); setRevision((value) => value + 1); }} />}
  </div>;
}

function UserInitial({ name }) { return <>{String(name || "C").trim().slice(0, 1).toUpperCase()}</>; }
