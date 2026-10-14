import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, ChevronDown, Lightbulb, PencilLine, Search, Sparkles, Undo2 } from "lucide-react";
import { CareerCoach } from "./CareerCoach.jsx";
import { api, getApiErrorMessage } from "../api/client.js";
import { formatLearningHours } from "../utils/learningPresentation.js";
import "../styles/career-coach.css";

const tabs = [["guidance", "Sugerencias", Lightbulb], ["writing", "Mejorar un texto", PencilLine]];
const learningLink = (course) => `/aprendizaje?search=${encodeURIComponent(course.title)}#cursos`;

export function CareerCoachWorkspace({ profile, editing, onProfileChanged, onEdit, onSave, context = "profile", vacancyJob, onDraftSaved, onDone }) {
  const [opened, setOpened] = useState(context !== "profile"), [tab, setTab] = useState(context === "learning" ? "radar" : context === "vacancy" ? "vacancy" : "guidance");
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  const [index, setIndex] = useState(0), [result, setResult] = useState(""), [style, setStyle] = useState("paragraph"), [texts, setTexts] = useState({}), [proposalId, setProposalId] = useState("");
  const [activeDraft, setActiveDraft] = useState("");
  const [intros, setIntros] = useState({}), [checks, setChecks] = useState({});
  const [filters, setFilters] = useState({ search: "", sector: profile.preferred_sector || "", location: "" }), [radar, setRadar] = useState(null), [radarView, setRadarView] = useState("learn"), [moreSkills, setMoreSkills] = useState(false);
  const [focusWriting, setFocusWriting] = useState(false);
  const reviewRef = useRef(null);
  const disabled = editing || busy;

  async function load() { setData((await api.get("/profiles/me/coach")).data); }
  useEffect(() => { if (!editing && context !== "learning") load().catch((failure) => setError(getApiErrorMessage(failure))); }, [editing, profile.experiences, profile.skills, context]);
  useEffect(() => {
    if (focusWriting && tab === "writing" && data) { document.getElementById("coach-experience")?.focus(); setFocusWriting(false); }
  }, [focusWriting, tab, data]);
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
    try { await action(); if (context !== "learning") await load(); if (refreshProfile) await onProfileChanged(); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function prepareVacancy(job) {
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
      {!!row.questions?.length && <aside className="coach-writing-idea"><strong>Una idea para concretar tu aporte</strong>{row.questions.map((question) => <p key={question}>{question}</p>)}<small>Si recuerdas ese dato, añádelo al resultado opcional y genera otra propuesta.</small></aside>}
      {row.status === "prepared" && <div className="coach-actions"><button className="button-primary" type="button" disabled={disabled || !(texts[row.id] ?? row.after).trim()} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "apply", text: texts[row.id] ?? row.after }); setMessage("Texto guardado en tu experiencia. Puedes deshacer este cambio."); }, true)}><CheckCircle2 size={16} />Usar este texto en mi perfil</button><span className="coach-help">Puedes editarlo antes de guardar.</span></div>}
      {row.status === "applied" && <div className="coach-actions"><span className="coach-success"><CheckCircle2 size={16} />Guardado en tu perfil</span><button className="button-secondary" type="button" disabled={disabled} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "undo" }); setMessage("Recuperaste tu texto anterior."); }, true)}><Undo2 size={15} />Deshacer este cambio</button></div>}
      {row.status === "undone" && <p>Recuperaste el texto anterior.</p>}
    </section>;
  }

  const Container = context === "profile" ? "details" : "section";
  return <Container id={context === "profile" ? "career-coach-workspace" : undefined} className={`coach-workspace coach-context-${context} print-hidden`} open={context === "profile" ? opened : undefined} onToggle={context === "profile" ? (event) => setOpened(event.currentTarget.open) : undefined}>
    {context === "profile" && <summary><span className="coach-workspace-brand"><span className="coach-brand-icon"><Sparkles size={23} /></span><span><small className="coach-eyebrow">AYUDA PARA TU HOJA DE VIDA</small><strong>Ideas para mejorar tu hoja de vida</strong><small>Sugerencias y redacción asistida cuando las necesites.</small></span></span><ChevronDown className="coach-disclosure-icon" size={20} /></summary>}
    <div className="coach-workspace-body">
      {context === "profile" && <div className="coach-tabs" role="tablist" aria-label="Ayuda para mi perfil" onKeyDown={(event) => {
        const buttons = [...event.currentTarget.querySelectorAll('[role="tab"]')], current = buttons.indexOf(document.activeElement);
        if (current < 0) return;
        const next = event.key === "ArrowRight" ? (current + 1) % buttons.length : event.key === "ArrowLeft" ? (current - 1 + buttons.length) % buttons.length : event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : null;
        if (next != null) { event.preventDefault(); buttons[next].focus(); buttons[next].click(); }
      }}>{tabs.map(([key, label, Icon]) => <button id={`coach-tab-${key}`} key={key} type="button" role="tab" tabIndex={tab === key ? 0 : -1} aria-selected={tab === key} aria-controls="coach-panel" onClick={() => { setTab(key); setError(""); setMessage(""); }}><Icon size={16} />{label}</button>)}</div>}
      {editing && ["writing", "vacancy"].includes(tab) && <div role="status" className="coach-save-notice"><span>Tienes cambios sin guardar. Guárdalos para trabajar con tu perfil actualizado.</span><button className="button-primary button-sm" type="button" disabled={busy} onClick={() => act(async () => { const saved = await onSave(); if (!saved) throw new Error("No se guardaron los cambios. Revisa los campos del perfil."); })}>Guardar y continuar</button></div>}
      {error && <p role="alert" className="coach-feedback coach-error">{error}</p>}
      {message && <p role="status" className="coach-feedback coach-success">{message}</p>}
      <div id={`coach-panel-${context}`} role={context === "profile" ? "tabpanel" : undefined} tabIndex={context === "profile" ? 0 : undefined} aria-labelledby={context === "profile" ? `coach-tab-${tab}` : undefined} aria-busy={busy}>
        {tab === "guidance" && <CareerCoach guidance={profile.cv_guidance} onEdit={onEdit} onStartWriting={startWriting} />}
        {tab === "writing" && <>
          <h3>Dale más fuerza a tu experiencia</h3><p>Elige una experiencia. La IA propondrá otra forma de contar tu aporte y una pregunta para ayudarte a concretarlo.</p>
          <p className="coach-help">IA local, sin cobros por API. La propuesta es un borrador: revísala antes de usarla.</p>
          {!data && <p role="status">Cargando tus experiencias…</p>}
          {data && !data.experiences.length && <div className="coach-empty"><PencilLine size={28} /><h4>Empieza con una experiencia</h4><p>Puede ser un empleo, una práctica o una colaboración real. Escribe una frase sobre lo que hiciste y te ayudaremos a presentarla.</p><button type="button" className="button-primary" onClick={() => onEdit("profile-experiences")}>Añadir mi experiencia<ArrowRight size={15} /></button></div>}
          {!!data?.experiences.length && <form className="coach-form" onSubmit={(event) => { event.preventDefault(); act(async () => { const { data: response } = await api.post("/profiles/me/coach/writing/generate", { experience_index: Number(index), source_version: data.source_version, style, result }, { timeout: 100000 }); setProposalId(response.id); setMessage("Revisa la propuesta. Tu perfil sigue igual hasta que decidas usarla."); }); }}>
            <label>¿Qué experiencia quieres mejorar?<select id="coach-experience" className="field-control" value={index} onChange={(event) => { setIndex(Number(event.target.value)); setResult(""); setProposalId(""); }}>{data.experiences.map((row, i) => <option key={i} value={i}>{row.role || "Cargo por completar"} · {row.company || "Organización"}</option>)}</select></label>
            <blockquote><strong>Lo que escribiste</strong>{experience?.description || "Añade una frase sobre tus responsabilidades para poder generar una propuesta."}</blockquote>
            <fieldset className="coach-style-picker"><legend>¿Cómo quieres presentarlo?</legend>{[["paragraph", "Un párrafo breve"], ["bullets", "Una lista de acciones"]].map(([value, label]) => <label key={value}><input type="radio" name="coach-writing-style" value={value} checked={style === value} onChange={() => setStyle(value)} />{label}</label>)}</fieldset>
            <details className="coach-optional"><summary>¿Quieres añadir un resultado? Es opcional</summary><label>Un resultado real que quieras incluir<textarea className="field-control" rows={2} maxLength={700} value={result} onChange={(event) => setResult(event.target.value)} placeholder="Por ejemplo: el equipo pudo consultar los pedidos en un solo lugar." /></label><p>No hace falta una cifra. También sirve una entrega o un cambio concreto.</p></details>
            <button type="submit" className="button-primary" disabled={disabled || !experience?.description?.trim()}><Sparkles size={16} />{busy ? "Preparando…" : "Generar una propuesta con IA"}</button>
            {!experience?.description?.trim() && <button className="button-secondary" type="button" onClick={() => onEdit(`experience-description-${index}`)}>Escribir mi experiencia primero</button>}
          </form>}
          {proposal && writingCard(proposal, true)}
          {!!data?.writing?.filter((row) => row.id !== proposalId).length && <details className="coach-history"><summary>Mis propuestas anteriores ({data.writing.filter((row) => row.id !== proposalId).length})</summary>{data.writing.filter((row) => row.id !== proposalId).map((row) => <details className="coach-record" key={row.id}><summary>{row.record.role || "Experiencia"} · {{ prepared: "Por revisar", applied: "Guardada", undone: "Deshecha" }[row.status]}</summary>{writingCard(row)}</details>)}</details>}
        </>}
        {tab === "vacancy" && <>
          <h3>Tu presentación para esta vacante</h3><p>Revisa una propuesta antes de enviar tu postulación. No cambia tu perfil principal.</p>
          <ol className="coach-steps" aria-label="Pasos para preparar mi presentación">{["Prepara tu texto", "Revísalo", "Úsalo al postularte"].map((label, i) => <li key={label} aria-current={(!vacancy ? i === 0 : vacancy.confirmed ? i === 2 : i === 1) ? "step" : undefined}><span>{i + 1}</span>{label}</li>)}</ol>
          {!vacancy && <div className="coach-job-selected"><div><h4>{vacancyJob.title}</h4><p>Vamos a preparar una presentación para esta vacante con tus datos confirmados.</p></div><button type="button" className="button-primary" disabled={disabled} onClick={() => prepareVacancy(vacancyJob)}><Sparkles size={16} />Crear mi presentación</button></div>}
          {vacancy && <section className="coach-vacancy-review">
            <button className="button-secondary button-sm" type="button" onClick={() => setActiveDraft("")}>Preparar otra propuesta</button>
            <h4>{vacancy.job_title}</h4><label>Tu presentación para esta vacante<textarea className="field-control" rows={5} maxLength={2000} value={intros[vacancy.id] ?? vacancy.intro} onChange={(event) => { setIntros((value) => ({ ...value, [vacancy.id]: event.target.value })); setChecks((value) => ({ ...value, [vacancy.id]: false })); }} /></label>
            <p>Puedes cambiar el texto. Tu hoja de vida principal se conserva.</p>
            {!!vacancy.supported_skills.length && <p>Habilidades tuyas que aparecen en esta vacante: <strong>{vacancy.supported_skills.join(", ")}</strong>.</p>}
            {!!vacancy.questions.length && <details className="coach-optional"><summary>Requisitos que conviene revisar ({vacancy.questions.length})</summary><p>No los hemos añadido a tu presentación porque no están registrados en tu perfil.</p>{vacancy.questions.map((question) => <p key={question}>{question}</p>)}</details>}
            <label className="coach-check"><input type="checkbox" checked={checks[vacancy.id] ?? vacancy.confirmed} onChange={(event) => setChecks((value) => ({ ...value, [vacancy.id]: event.target.checked }))} />He revisado el texto y refleja mi experiencia real.</label>
            <div className="coach-actions"><button type="button" className="button-primary" disabled={disabled || !(checks[vacancy.id] ?? vacancy.confirmed) || !(intros[vacancy.id] ?? vacancy.intro).trim()} onClick={() => act(async () => { const { data: saved } = await api.put(`/profiles/me/coach/drafts/${vacancy.id}`, { revision: vacancy.revision, intro: intros[vacancy.id] ?? vacancy.intro, confirmed: true }); setIntros((value) => ({ ...value, [vacancy.id]: saved.intro })); onDraftSaved?.(saved); setMessage("Presentación guardada para esta postulación."); })}><CheckCircle2 size={16} />Guardar presentación</button>
              {vacancy.confirmed && (intros[vacancy.id] ?? vacancy.intro) === vacancy.intro && <button type="button" className="button-secondary" onClick={onDone}>Listo, continuar mi postulación<ArrowRight size={15} /></button>}
            </div>
          </section>}
          {!!data?.drafts.filter((row) => row.job_id === vacancyJob.id).length && <details className="coach-history"><summary>Mis presentaciones guardadas ({data.drafts.filter((row) => row.job_id === vacancyJob.id).length})</summary>{data.drafts.filter((row) => row.job_id === vacancyJob.id).map((row) => <article className="coach-saved-version" key={row.id}><div><h4>{row.job_title}</h4><p>{row.confirmed ? "Revisada y guardada" : "Pendiente de revisar"}</p></div><button type="button" className="button-secondary button-sm" onClick={() => setActiveDraft(row.id)}>Abrir presentación</button></article>)}</details>}
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
  </Container>;
}
