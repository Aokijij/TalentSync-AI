import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, ChevronDown, Download, FileCheck2, Lightbulb, MapPin, PencilLine, Search, Sparkles, Target, TrendingUp, Undo2, Upload } from "lucide-react";
import { CareerCoach } from "./CareerCoach.jsx";
import { api, getApiErrorMessage } from "../api/client.js";
import { formatLearningHours } from "../utils/learningPresentation.js";
import "../styles/career-coach.css";

const tabs = [["guidance", "Qué mejorar", Lightbulb], ["writing", "Mejorar textos", PencilLine], ["vacancy", "Preparar postulación", Target], ["reading", "Revisar mi CV", FileCheck2], ["radar", "Qué aprender", TrendingUp]];
const learningLink = (course) => `/aprendizaje?search=${encodeURIComponent(course.title)}#cursos`;

export function CareerCoachWorkspace({ profile, editing, launch, onProfileChanged, onEdit, onSave, onUpload }) {
  const [opened, setOpened] = useState(true), [tab, setTab] = useState("guidance");
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  const [index, setIndex] = useState(0), [result, setResult] = useState(""), [style, setStyle] = useState("paragraph"), [texts, setTexts] = useState({}), [proposalId, setProposalId] = useState("");
  const [search, setSearch] = useState(""), [jobs, setJobs] = useState(null), [jobId, setJobId] = useState(""), [selectedJob, setSelectedJob] = useState(null), [activeDraft, setActiveDraft] = useState("");
  const [intros, setIntros] = useState({}), [checks, setChecks] = useState({});
  const [reading, setReading] = useState(null), [readingBusy, setReadingBusy] = useState(false), [pdf, setPdf] = useState("");
  const [filters, setFilters] = useState({ search: "", sector: profile.preferred_sector || "", location: "" }), [radar, setRadar] = useState(null), [radarView, setRadarView] = useState("learn"), [moreSkills, setMoreSkills] = useState(false);
  const [focusWriting, setFocusWriting] = useState(false);
  const reviewRef = useRef(null);
  const hasPdf = Boolean(profile.cv_filename);
  const disabled = editing || busy;

  async function load() { setData((await api.get("/profiles/me/coach")).data); }
  useEffect(() => { if (!editing) load().catch((failure) => setError(getApiErrorMessage(failure))); }, [editing, profile.experiences, profile.skills]);
  useEffect(() => {
    if (focusWriting && tab === "writing" && data) { document.getElementById("coach-experience")?.focus(); setFocusWriting(false); }
  }, [focusWriting, tab, data]);
  useEffect(() => {
    if (launch) {
      setOpened(true); setTab(launch.tab);
      if (launch.index != null) setIndex(launch.index);
      if (launch.jobId) setJobId(String(launch.jobId));
      document.getElementById("career-coach-workspace")?.scrollIntoView({ block: "start", behavior: "smooth" });
    }
  }, [launch]);
  useEffect(() => {
    if (!opened || tab !== "vacancy" || jobs) return;
    let active = true;
    api.get("/profiles/me/coach/jobs").then(({ data: response }) => { if (active) setJobs(response); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [opened, tab, jobs]);
  useEffect(() => {
    if (!jobId) return;
    let active = true;
    api.get(`/jobs/${jobId}`).then(({ data: response }) => { if (active) setSelectedJob(response); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure, "No pudimos cargar esa vacante. Elige otra de la lista.")); });
    return () => { active = false; };
  }, [jobId]);
  useEffect(() => {
    if (!opened || tab !== "reading" || !hasPdf) return;
    let active = true;
    setReadingBusy(true); setReading(null); setError("");
    api.get("/profiles/me/coach/reading").then(({ data: response }) => { if (active) setReading(response); })
      .catch((failure) => { if (active) setError(getApiErrorMessage(failure, "No pudimos revisar el documento. Puedes subir otro PDF.")); })
      .finally(() => { if (active) setReadingBusy(false); });
    return () => { active = false; };
  }, [opened, tab, hasPdf, profile.cv_uploaded_at]);
  useEffect(() => () => { if (pdf) URL.revokeObjectURL(pdf); }, [pdf]);
  useEffect(() => { setPdf(""); }, [profile.cv_uploaded_at]);
  useEffect(() => {
    if (!opened || tab !== "radar" || radar) return;
    let active = true;
    api.get("/profiles/me/coach/radar", { params: { sector: profile.preferred_sector || "" } }).then(({ data: response }) => { if (active) setRadar(response); })
      .catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [opened, tab, profile.preferred_sector, radar]);
  useEffect(() => { if (proposalId) reviewRef.current?.focus(); }, [proposalId, data]);

  function startWriting(experienceIndex) {
    setIndex(experienceIndex ?? 0); setResult(""); setProposalId(""); setTab("writing"); setError(""); setMessage(""); setFocusWriting(true);
  }
  async function act(action, refreshProfile = false) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); await load(); if (refreshProfile) await onProfileChanged(); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function download(draftId, applicationId) {
    await act(async () => {
      const { data: file } = await api.get("/profiles/me/coach/export", { params: applicationId ? { application_id: applicationId } : draftId ? { draft_id: draftId } : {}, responseType: "blob" });
      const url = URL.createObjectURL(file), anchor = document.createElement("a");
      anchor.href = url; anchor.download = "mi-hoja-de-vida.pdf"; document.body.append(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000); setMessage("Tu PDF está listo. Revisa las descargas del navegador.");
    });
  }
  async function prepareVacancy(job) {
    setSelectedJob(job);
    await act(async () => {
      const { data: response } = await api.post("/profiles/me/coach/drafts", { job_id: job.id });
      setActiveDraft(response.id); setMessage("Preparamos una presentación con la información de tu perfil. Revísala antes de guardarla.");
    });
  }
  const proposal = data?.writing?.find((row) => row.id === proposalId);
  const vacancy = data?.drafts?.find((row) => row.id === activeDraft);
  const experience = data?.experiences?.[index];
  const learningSkills = radar?.skills.filter((row) => !row.declared) || [];
  const knownSkills = radar?.skills.filter((row) => row.declared) || [];
  const visibleSkills = radarView === "learn" ? learningSkills : knownSkills;

  function writingCard(row, primary = false) {
    return <section className="coach-proposal" key={row.id}>
      {primary && <h4 ref={reviewRef} tabIndex={-1}>Tu propuesta está lista</h4>}
      <div className="coach-columns">
        <div><h4>Texto actual</h4><blockquote>{row.before || "Sin descripción"}</blockquote></div>
        <label><span className="coach-proposal-label">Propuesta para tu perfil</span><textarea className="field-control" rows={6} maxLength={3000} disabled={row.status !== "prepared" || busy} value={texts[row.id] ?? row.after} onChange={(event) => setTexts((value) => ({ ...value, [row.id]: event.target.value }))} /></label>
      </div>
      {!!row.changes?.length && <p>{row.changes.join(" ")}</p>}
      {row.status === "prepared" && <div className="coach-actions"><button className="button-primary" type="button" disabled={disabled || !(texts[row.id] ?? row.after).trim()} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "apply", text: texts[row.id] ?? row.after }); setMessage("Texto guardado en tu experiencia. Puedes deshacer este cambio."); }, true)}><CheckCircle2 size={16} />Usar este texto en mi perfil</button><span className="coach-help">Puedes editarlo antes de guardar.</span></div>}
      {row.status === "applied" && <div className="coach-actions"><span className="coach-success"><CheckCircle2 size={16} />Guardado en tu perfil</span><button className="button-secondary" type="button" disabled={disabled} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "undo" }); setMessage("Recuperaste tu texto anterior."); }, true)}><Undo2 size={15} />Deshacer este cambio</button></div>}
      {row.status === "undone" && <p>Recuperaste el texto anterior.</p>}
    </section>;
  }

  return <details id="career-coach-workspace" className="coach-workspace print-hidden" open={opened} onToggle={(event) => setOpened(event.currentTarget.open)}>
    <summary><span className="coach-workspace-brand"><span className="coach-brand-icon"><Sparkles size={23} /></span><span><small className="coach-eyebrow">AYUDA PARA TU PRÓXIMO PASO</small><strong>Mejora tu perfil con ayuda</strong><small>Genera textos, prepara tu postulación y descubre qué aprender.</small></span></span><ChevronDown className="coach-disclosure-icon" size={20} /></summary>
    <div className="coach-workspace-body">
      <div className="coach-tabs" role="tablist" aria-label="Ayuda para mi perfil" onKeyDown={(event) => {
        const buttons = [...event.currentTarget.querySelectorAll('[role="tab"]')], current = buttons.indexOf(document.activeElement);
        if (current < 0) return;
        const next = event.key === "ArrowRight" ? (current + 1) % buttons.length : event.key === "ArrowLeft" ? (current - 1 + buttons.length) % buttons.length : event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : null;
        if (next != null) { event.preventDefault(); buttons[next].focus(); buttons[next].click(); }
      }}>{tabs.map(([key, label, Icon]) => <button id={`coach-tab-${key}`} key={key} type="button" role="tab" tabIndex={tab === key ? 0 : -1} aria-selected={tab === key} aria-controls="coach-panel" onClick={() => { setTab(key); setError(""); setMessage(""); }}><Icon size={16} />{label}</button>)}</div>
      {editing && ["writing", "vacancy"].includes(tab) && <div role="status" className="coach-save-notice"><span>Tienes cambios sin guardar. Guárdalos para trabajar con tu perfil actualizado.</span><button className="button-primary button-sm" type="button" disabled={busy} onClick={() => act(async () => { const saved = await onSave(); if (!saved) throw new Error("No se guardaron los cambios. Revisa los campos del perfil."); })}>Guardar y continuar</button></div>}
      {error && <p role="alert" className="coach-feedback coach-error">{error}</p>}
      {message && <p role="status" className="coach-feedback coach-success">{message}</p>}
      <div id="coach-panel" role="tabpanel" tabIndex={0} aria-labelledby={`coach-tab-${tab}`} aria-busy={busy}>
        {tab === "guidance" && <CareerCoach guidance={profile.cv_guidance} onEdit={onEdit} onStartWriting={startWriting} />}
        {tab === "writing" && <>
          <h3>Te ayudamos a escribirlo mejor</h3><p>Elige una experiencia y genera una propuesta con lo que ya escribiste. No necesitas llenar otro formulario.</p>
          {!data && <p role="status">Cargando tus experiencias…</p>}
          {data && !data.experiences.length && <div className="coach-empty"><PencilLine size={28} /><h4>Empieza con una experiencia</h4><p>Puede ser un empleo, una práctica o una colaboración real. Escribe una frase sobre lo que hiciste y te ayudaremos a presentarla.</p><button type="button" className="button-primary" onClick={() => onEdit("profile-experiences")}>Añadir mi experiencia<ArrowRight size={15} /></button></div>}
          {!!data?.experiences.length && <form className="coach-form" onSubmit={(event) => { event.preventDefault(); act(async () => { const { data: response } = await api.post("/profiles/me/coach/writing/generate", { experience_index: Number(index), source_version: data.source_version, style, result }); setProposalId(response.id); setMessage("Revisa la propuesta. Tu perfil sigue igual hasta que decidas usarla."); }); }}>
            <label>¿Qué experiencia quieres mejorar?<select id="coach-experience" className="field-control" value={index} onChange={(event) => { setIndex(Number(event.target.value)); setResult(""); setProposalId(""); }}>{data.experiences.map((row, i) => <option key={i} value={i}>{row.role || "Cargo por completar"} · {row.company || "Organización"}</option>)}</select></label>
            <blockquote><strong>Lo que escribiste</strong>{experience?.description || "Añade una frase sobre tus responsabilidades para poder generar una propuesta."}</blockquote>
            <fieldset className="coach-style-picker"><legend>¿Cómo quieres presentarlo?</legend>{[["paragraph", "Un párrafo breve"], ["bullets", "Una lista de acciones"]].map(([value, label]) => <label key={value}><input type="radio" name="coach-writing-style" value={value} checked={style === value} onChange={() => setStyle(value)} />{label}</label>)}</fieldset>
            <details className="coach-optional"><summary>¿Quieres añadir un resultado? Es opcional</summary><label>Un resultado real que quieras incluir<textarea className="field-control" rows={2} maxLength={700} value={result} onChange={(event) => setResult(event.target.value)} placeholder="Por ejemplo: el equipo pudo consultar los pedidos en un solo lugar." /></label><p>No hace falta una cifra. También sirve una entrega o un cambio concreto.</p></details>
            <button type="submit" className="button-primary" disabled={disabled || !experience?.description?.trim()}><Sparkles size={16} />{busy ? "Preparando…" : "Generar una mejora de mi texto"}</button>
            {!experience?.description?.trim() && <button className="button-secondary" type="button" onClick={() => onEdit(`experience-description-${index}`)}>Escribir mi experiencia primero</button>}
          </form>}
          {proposal && writingCard(proposal, true)}
          {!!data?.writing?.filter((row) => row.id !== proposalId).length && <details className="coach-history"><summary>Mis propuestas anteriores ({data.writing.filter((row) => row.id !== proposalId).length})</summary>{data.writing.filter((row) => row.id !== proposalId).map((row) => <details className="coach-record" key={row.id}><summary>{row.record.role || "Experiencia"} · {{ prepared: "Por revisar", applied: "Guardada", undone: "Deshecha" }[row.status]}</summary>{writingCard(row)}</details>)}</details>}
        </>}
        {tab === "vacancy" && <>
          <h3>Prepara tu presentación para un empleo</h3><p>Elige una vacante. Te proponemos un texto con tu experiencia para que lo revises y lo uses al postularte.</p>
          <ol className="coach-steps" aria-label="Pasos para preparar mi presentación">{["Elige un empleo", "Revisa tu texto", "Guárdalo y postúlate"].map((label, i) => <li key={label} aria-current={(!vacancy ? i === 0 : vacancy.confirmed ? i === 2 : i === 1) ? "step" : undefined}><span>{i + 1}</span>{label}</li>)}</ol>
          {!vacancy && <>
            {selectedJob && <article className="coach-job-selected"><div><small>Vacante elegida</small><h4>{selectedJob.title}</h4><p>{selectedJob.location || "Ubicación por consultar"}</p></div><button type="button" className="button-primary" disabled={disabled} onClick={() => prepareVacancy(selectedJob)}>Crear mi presentación<ArrowRight size={15} /></button></article>}
            <form className="coach-search" onSubmit={(event) => { event.preventDefault(); act(async () => { setJobs((await api.get("/profiles/me/coach/jobs", { params: { search } })).data); setSelectedJob(null); }); }}><label>Encuentra el empleo que te interesa<input className="field-control" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Escribe una palabra del cargo" maxLength={160} /></label><button className="button-secondary" disabled={busy}><Search size={15} />Buscar</button></form>
            {!jobs && <p role="status">Buscando vacantes disponibles…</p>}
            {jobs && <p>{jobs.total ? `${jobs.total} vacantes disponibles${jobs.total > 6 ? ". Mostramos las primeras 6; usa la búsqueda para encontrar otra." : "."}` : "No encontramos vacantes con esa palabra. Prueba otra o deja la búsqueda vacía."}</p>}
            <div className="coach-job-list">{jobs?.items.slice(0, 6).map((job) => <article key={job.id}><div><h4>{job.title}</h4><p><MapPin size={14} />{job.location || "Ubicación por consultar"}</p></div><button type="button" className="button-secondary" disabled={disabled} onClick={() => prepareVacancy(job)}>Elegir este empleo<ArrowRight size={15} /></button></article>)}</div>
          </>}
          {vacancy && <section className="coach-vacancy-review">
            <button className="button-secondary button-sm" type="button" onClick={() => { setActiveDraft(""); setSelectedJob(null); }}><ArrowLeft size={15} />Elegir otro empleo</button>
            <h4>{vacancy.job_title}</h4><label>Tu presentación para esta vacante<textarea className="field-control" rows={5} maxLength={2000} value={intros[vacancy.id] ?? vacancy.intro} onChange={(event) => { setIntros((value) => ({ ...value, [vacancy.id]: event.target.value })); setChecks((value) => ({ ...value, [vacancy.id]: false })); }} /></label>
            <p>Puedes cambiar el texto. Tu hoja de vida principal se conserva.</p>
            {!!vacancy.supported_skills.length && <p>Habilidades tuyas que aparecen en esta vacante: <strong>{vacancy.supported_skills.join(", ")}</strong>.</p>}
            {!!vacancy.questions.length && <details className="coach-optional"><summary>Requisitos que conviene revisar ({vacancy.questions.length})</summary><p>No los hemos añadido a tu presentación porque no están registrados en tu perfil.</p>{vacancy.questions.map((question) => <p key={question}>{question}</p>)}</details>}
            <label className="coach-check"><input type="checkbox" checked={checks[vacancy.id] ?? vacancy.confirmed} onChange={(event) => setChecks((value) => ({ ...value, [vacancy.id]: event.target.checked }))} />He revisado el texto y refleja mi experiencia real.</label>
            <div className="coach-actions"><button type="button" className="button-primary" disabled={disabled || !(checks[vacancy.id] ?? vacancy.confirmed) || !(intros[vacancy.id] ?? vacancy.intro).trim()} onClick={() => act(async () => { const { data: saved } = await api.put(`/profiles/me/coach/drafts/${vacancy.id}`, { revision: vacancy.revision, intro: intros[vacancy.id] ?? vacancy.intro, confirmed: true }); setIntros((value) => ({ ...value, [vacancy.id]: saved.intro })); setMessage("Presentación guardada. Ya puedes continuar a la vacante para postularte."); })}><CheckCircle2 size={16} />Guardar presentación</button>
              {vacancy.confirmed && (intros[vacancy.id] ?? vacancy.intro) === vacancy.intro && <><Link className="button-secondary" to={`/vacantes/${vacancy.job_id}?coachDraft=${vacancy.id}`}>Continuar a la vacante<ArrowRight size={15} /></Link><button type="button" className="button-secondary" disabled={busy} onClick={() => download(vacancy.id)}><Download size={15} />Descargar PDF</button></>}
            </div>
          </section>}
          {!!data?.drafts.length && <details className="coach-history"><summary>Mis presentaciones guardadas ({data.drafts.length})</summary>{data.drafts.map((row) => <article className="coach-saved-version" key={row.id}><div><h4>{row.job_title}</h4><p>{row.confirmed ? "Revisada y guardada" : "Pendiente de revisar"}</p></div><button type="button" className="button-secondary button-sm" onClick={() => setActiveDraft(row.id)}>Abrir presentación</button></article>)}</details>}
          {!!data?.submitted?.length && <details className="coach-history"><summary>Lo que ya enviaste ({data.submitted.length})</summary>{data.submitted.map((row) => <article className="coach-saved-version" key={row.application_id}><div><h4>{row.job_title}</h4><p>Enviada el {new Date(row.created_at).toLocaleDateString("es-CO")}</p></div><button type="button" className="button-secondary button-sm" disabled={busy} onClick={() => download(null, row.application_id)}><Download size={14} />Descargar copia</button></article>)}</details>}
        </>}
        {tab === "reading" && <>
          <h3>Comprueba que tu hoja de vida se haya importado bien</h3><p>Te señalamos qué datos reconocimos y qué campos conviene revisar. Elige un apartado para corregirlo en tu perfil.</p>
          {!hasPdf && <div className="coach-empty"><Upload size={28} /><h4>Sube tu hoja de vida para empezar</h4><p>Usa un PDF con texto seleccionable. Después podrás revisar los datos importados aquí.</p><label className="button-primary" role="button" tabIndex={0} onKeyDown={(event) => { if (["Enter", " "].includes(event.key)) { event.preventDefault(); event.currentTarget.querySelector("input").click(); } }}><Upload size={16} />Elegir mi PDF<input className="hidden" type="file" accept="application/pdf" onChange={onUpload} /></label></div>}
          {readingBusy && <p role="status">Revisando los datos de tu documento…</p>}
          {reading && <>
            {!reading.has_text && <p className="coach-notice">No encontramos texto seleccionable. Si el PDF es una imagen, sube una versión con texto o completa los campos manualmente.</p>}
            <div className="coach-document-checks">{reading.checks?.map((check) => <article key={check.target}><span className={`coach-status-label ${check.ok ? "coach-status-found" : ""}`}>{check.ok ? "Encontrado en el texto" : "Para revisar"}</span><h4>{check.title}</h4><p>{check.detail}</p><button className="button-secondary button-sm" type="button" onClick={() => onEdit(check.target)}>{check.action}<ArrowRight size={14} /></button></article>)}</div>
            <div className="coach-download-panel"><FileCheck2 size={25} /><div><h4>Una hoja de vida sencilla para compartir</h4><p>Descarga tus datos guardados en un PDF de una columna y revisa el documento antes de enviarlo.</p></div><button className="button-primary" type="button" disabled={busy} onClick={() => download()}><Download size={16} />Descargar mi hoja de vida</button></div>
            <details className="coach-history"><summary>Ver el documento original y el detalle de lectura</summary><p>{reading.method} · {reading.pages} {reading.pages === 1 ? "página" : "páginas"}{reading.truncated ? " · Vista limitada" : ""}</p><p>{reading.note}</p>
              {!pdf && <button type="button" className="button-secondary" disabled={busy} onClick={() => act(async () => { const { data: file } = await api.get("/profiles/me/coach/pdf", { responseType: "blob" }); setPdf(URL.createObjectURL(file)); })}>Abrir documento original</button>}
              {pdf && <iframe className="coach-original-pdf" title="Tu hoja de vida original" src={pdf} />}
              <details className="coach-optional"><summary>Ver el texto que se pudo leer</summary><pre className="coach-raw-text">{reading.text || "No se encontró texto."}</pre></details>
            </details>
          </>}
        </>}
        {tab === "radar" && <>
          <h3>Descubre qué puedes aprender para tu próximo empleo</h3><p>Miramos las habilidades solicitadas en las ofertas disponibles y te acercamos cursos para empezar.</p>
          <form className="coach-learning-search" onSubmit={(event) => { event.preventDefault(); act(async () => { setRadar((await api.get("/profiles/me/coach/radar", { params: filters })).data); setMoreSkills(false); }); }}>
            <div className="coach-search"><label>¿Qué trabajo te interesa?<input className="field-control" maxLength={160} value={filters.search} onChange={(event) => setFilters((value) => ({ ...value, search: event.target.value }))} placeholder="Una palabra del cargo, o déjalo vacío" /></label><button className="button-primary" disabled={busy}><Search size={15} />Buscar qué aprender</button></div>
            <details className="coach-optional"><summary>Ajustar sector y ubicación{filters.sector ? ` · ${filters.sector}` : ""}</summary><div className="coach-columns">{[["sector", "Sector"], ["location", "Ciudad o ubicación"]].map(([key, label]) => <label key={key}>{label}<input className="field-control" maxLength={160} value={filters[key]} onChange={(event) => setFilters((value) => ({ ...value, [key]: event.target.value }))} placeholder="Cualquiera" /></label>)}</div><p>Después de cambiar los campos, pulsa «Buscar qué aprender».</p></details>
          </form>
          {!radar && <p role="status">Buscando habilidades y formación…</p>}
          {radar && <>
            <div className="coach-learning-summary"><strong>{radar.sample} ofertas consultadas</strong><span>{radar.sample ? "Elige una habilidad y abre el curso que te interese." : "Prueba otra palabra, ubicación o sector."}</span></div>
            {!!radar.sample && <><div className="coach-learning-switch" aria-label="Habilidades por explorar"><button type="button" aria-pressed={radarView === "learn"} onClick={() => { setRadarView("learn"); setMoreSkills(false); }}>Por aprender ({learningSkills.length})</button><button type="button" aria-pressed={radarView === "known"} onClick={() => { setRadarView("known"); setMoreSkills(false); }}>Ya están en mi perfil ({knownSkills.length})</button></div>
              {!visibleSkills.length && <div className="coach-empty"><CheckCircle2 size={28} /><h4>{radarView === "learn" ? "Las habilidades mostradas ya están en tu perfil" : "Aún no tienes estas habilidades registradas"}</h4><p>{radarView === "learn" ? "Puedes profundizar en ellas desde la otra pestaña o explorar un cargo diferente." : "Si conoces alguna, puedes añadirla en Habilidades. Si quieres aprenderla, consulta los cursos sugeridos."}</p></div>}
              <div className="coach-learning-grid">{visibleSkills.slice(0, moreSkills ? 12 : 3).map((row) => <article key={row.skill}>
                <span className="coach-learning-count">Solicitada en {row.count} de {radar.sample} ofertas{row.percentage == null ? "" : ` · ${row.percentage}%`}</span><h4>{row.skill}</h4><p>{row.declared ? "Ya la tienes registrada. Puedes seguir practicándola." : "No está registrada en tu perfil. Elige si quieres aprenderla o si ya la conoces."}</p>
                {row.courses[0] ? <div className="coach-course-suggestion"><small>UN CURSO PARA EMPEZAR</small><h5>{row.courses[0].title}</h5><p>{row.courses[0].provider}{row.courses[0].hours ? ` · ${formatLearningHours(row.courses[0].hours)} h estimadas` : ""}</p><Link className="button-primary button-sm" to={learningLink(row.courses[0])}>Ver este curso<ArrowRight size={14} /></Link></div> : <p>No hay un curso asociado en el catálogo por ahora.</p>}
                {row.courses.length > 1 && <details className="coach-optional"><summary>Otros cursos ({row.courses.length - 1})</summary>{row.courses.slice(1).map((course) => <Link className="coach-course-link" key={course.id} to={learningLink(course)}>{course.title}<ArrowRight size={14} /></Link>)}</details>}
                {!row.declared && <button type="button" className="button-secondary button-sm" onClick={() => onEdit("profile-skills")}>Ya la conozco: revisar mis habilidades</button>}
              </article>)}</div>
              {visibleSkills.length > 3 && <button className="button-secondary coach-show-more" type="button" aria-expanded={moreSkills} onClick={() => setMoreSkills((value) => !value)}>{moreSkills ? "Mostrar menos" : `Ver ${visibleSkills.length - 3} habilidades más`}<ChevronDown size={15} /></button>}
            </>}
            <details className="coach-history"><summary>¿De dónde salen estas sugerencias?</summary><p>{radar.note} {radar.small_sample ? "Hay pocas ofertas; no mostramos porcentajes." : ""}</p><p>Ofertas desde {radar.since}. Consulta del {new Date(radar.as_of).toLocaleDateString("es-CO")}.</p><p>Fuentes: {Object.entries(radar.sources).map(([name, count]) => `${name} (${count})`).join(", ") || "Sin ofertas"}.</p><h4>Algunas ofertas consultadas</h4>{radar.jobs.map((job) => <p key={job.id}><Link className="coach-course-link" to={`/vacantes/${job.id}`}>{job.title} · {job.location}</Link></p>)}</details>
          </>}
        </>}
      </div>
    </div>
  </details>;
}
