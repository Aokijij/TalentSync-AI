import { AutoResizeTextarea } from "./AutoResizeTextarea.jsx";
import { bulletKeyDown } from "../utils/bulletEditing.js";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, ChevronDown, Lightbulb, PencilLine, Search, Sparkles, Undo2, RotateCcw, ArrowUpRight, SlidersHorizontal, Trash2 } from "lucide-react";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { LearningSources } from "./LearningSources.jsx";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { COLOMBIA_LOCATIONS } from "../constants/colombianCities.js";
import { Autocomplete } from "./Autocomplete.jsx";
import { groupWritingHistory } from "../utils/writingHistory.js";
import { experiencePeriod } from "../utils/experienceDates.js";
import { skillName } from "../utils/skillNames.js";
import { browseRadarSkills } from "../utils/radarSkills.js";
import { CareerCoach } from "./CareerCoach.jsx";
import { api, getApiErrorMessage } from "../api/client.js";
import { formatLearningHours } from "../utils/learningPresentation.js";
import "../styles/career-coach.css";

const popularCities = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga", "Pereira"];
const allCities = [...new Set(Object.values(COLOMBIA_LOCATIONS).flat())];
const cities = [...popularCities.filter((city) => allCities.includes(city)), ...allCities.filter((city) => !popularCities.includes(city)).sort((a, b) => a.localeCompare(b, "es"))];
const tabs = [["guidance", "Sugerencias", Lightbulb], ["writing", "Mejorar un texto", PencilLine]];
const learningLink = (course) => `/aprendizaje?search=${encodeURIComponent(course.title)}#cursos`;

export function CareerCoachWorkspace({ profile, editing, onProfileChanged, onEdit, onSave, context = "profile", active = true, externalRadar, hideFilters = false }) {
  const feedback = useFeedback();
  const [tab, setTab] = useState(context === "learning" ? "radar" : "guidance");
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  const [index, setIndex] = useState(0), [result, setResult] = useState(""), [style, setStyle] = useState("paragraph"), [texts, setTexts] = useState({}), [proposalId, setProposalId] = useState("");
  const [filters, setFilters] = useState({ search: "", sector: profile.preferred_sector || "", location: "" }), [radar, setRadar] = useState(externalRadar ?? null), [radarView, setRadarView] = useState("learn");
  const [skillQuery, setSkillQuery] = useState(""), [skillPage, setSkillPage] = useState(1);
  const [selectedSkill, setSelectedSkill] = useState("");
  const [focusWriting, setFocusWriting] = useState(false);
  const reviewRef = useRef(null);
  const disabled = editing || busy;

  async function load() { setData((await api.get("/profiles/me/coach")).data); }
  useEffect(() => { if (active && !editing && context !== "learning") load().catch((failure) => setError(getApiErrorMessage(failure))); }, [active, editing, profile.experiences, profile.skills, context]);
  useEffect(() => {
    if (focusWriting && tab === "writing" && data) { document.getElementById("coach-experience")?.focus(); setFocusWriting(false); }
  }, [focusWriting, tab, data]);
  useEffect(() => {
    if (externalRadar !== undefined || tab !== "radar" || radar) return;
    let active = true;
    api.get("/profiles/me/coach/radar", { params: { sector: profile.preferred_sector || "" } }).then(({ data: response }) => { if (active) setRadar(response); })
      .catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [tab, profile.preferred_sector, radar, externalRadar]);
  useEffect(() => { if (externalRadar !== undefined) { setRadar(externalRadar); setSkillPage(1); setSkillQuery(""); setSelectedSkill(""); } }, [externalRadar]);
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
  const proposal = data?.writing?.find((row) => row.id === proposalId);
  const experience = data?.experiences?.[index];
  const learningSkills = radar?.skills.filter((row) => !row.declared) || [];
  const knownSkills = radar?.own_skills || radar?.skills.filter((row) => row.declared) || [];
  const visibleSkills = radarView === "learn" ? learningSkills : knownSkills;
  const skillBrowser = browseRadarSkills(visibleSkills, skillQuery, skillPage);
  const selected = visibleSkills.find((row) => row.skill === selectedSkill) || skillBrowser.rows[0] || visibleSkills[0];

  function writingCard(row, primary = false) {
    return <section className="coach-proposal" key={row.id}>
      {primary && <h4 ref={reviewRef} tabIndex={-1}>Tu propuesta está lista</h4>}
      <div className="coach-columns">
        <div><h4>Texto actual</h4><blockquote>{row.before || "Sin descripción"}</blockquote></div>
        <label><span className="coach-proposal-label">Propuesta para tu perfil</span><AutoResizeTextarea rows={6} maxLength={3000} disabled={row.status !== "prepared" || busy} value={texts[row.id] ?? row.after} onChange={(event) => setTexts((value) => ({ ...value, [row.id]: event.target.value }))} onKeyDown={(event) => bulletKeyDown(event, (text) => setTexts((value) => ({ ...value, [row.id]: text })))} /></label>
      </div>
      {!!row.changes?.length && <p>{row.changes.join(" ")}</p>}<p className="writing-context-note">Al aplicar la propuesta generada conservamos su contexto original. Si corriges el texto manualmente, tu corrección reemplaza ese respaldo. La redacción no añade habilidades ni garantiza subir la compatibilidad.</p>
      {!!row.questions?.length && <aside className="coach-writing-idea"><strong>Una idea para concretar tu aporte</strong>{row.questions.map((question) => <p key={question}>{question}</p>)}<small>Si recuerdas ese dato, añádelo al resultado opcional y genera otra propuesta.</small></aside>}
      {row.status === "prepared" && <div className="coach-actions"><button className="button-primary" type="button" disabled={disabled || !(texts[row.id] ?? row.after).trim()} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "apply", text: texts[row.id] ?? row.after }); setMessage("Texto guardado en tu experiencia. Puedes deshacer este cambio."); }, true)}><CheckCircle2 size={16} />Usar este texto en mi perfil</button><span className="coach-help">Puedes editarlo antes de guardar.</span></div>}
      {row.status === "applied" && <div className="coach-actions"><span className="coach-success"><CheckCircle2 size={16} />Guardado en tu perfil</span><button className="button-secondary" type="button" disabled={disabled} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "undo" }); setMessage("Recuperaste tu texto anterior."); }, true)}><Undo2 size={15} />Deshacer este cambio</button></div>}
      {row.status === "undone" && <p>Recuperaste el texto anterior.</p>}
      <button type="button" className="writing-delete-action" disabled={busy} onClick={async () => { if (!await feedback.confirm({ title: "Eliminar esta versión", description: row.status === "applied" ? "El texto aplicado permanecerá en tu perfil. Se eliminará esta versión del historial y su opción de deshacer." : "Se eliminará esta propuesta del historial. Tu experiencia guardada permanecerá igual.", confirmLabel: "Eliminar versión" })) return; act(async () => { await api.delete(`/profiles/me/coach/writing/${row.id}`); if (proposalId === row.id) setProposalId(""); setMessage("Versión eliminada del historial."); }); }}><Trash2 size={15} />Eliminar versión</button>
    </section>;
  }

  return <section className={`coach-workspace coach-context-${context} print-hidden`}>
    <div className="coach-workspace-body">
      {context === "profile" && <div className="coach-tabs" role="tablist" aria-label="Ayuda para mi perfil" onKeyDown={(event) => {
        const buttons = [...event.currentTarget.querySelectorAll('[role="tab"]')], current = buttons.indexOf(document.activeElement);
        if (current < 0) return;
        const next = event.key === "ArrowRight" ? (current + 1) % buttons.length : event.key === "ArrowLeft" ? (current - 1 + buttons.length) % buttons.length : event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : null;
        if (next != null) { event.preventDefault(); buttons[next].focus(); buttons[next].click(); }
      }}>{tabs.map(([key, label, Icon]) => <button id={`coach-tab-${key}`} key={key} type="button" role="tab" tabIndex={tab === key ? 0 : -1} aria-selected={tab === key} aria-controls="coach-panel-profile" onClick={() => { setTab(key); setError(""); setMessage(""); }}><Icon size={16} />{label}</button>)}</div>}
      {editing && tab === "writing" && <div role="status" className="coach-save-notice"><span>Tienes cambios sin guardar. Guárdalos para trabajar con tu perfil actualizado.</span><button className="button-primary button-sm" type="button" disabled={busy} onClick={() => act(async () => { const saved = await onSave(); if (!saved) throw new Error("No se guardaron los cambios. Revisa los campos del perfil."); })}>Guardar y continuar</button></div>}
      {error && <p role="alert" className="coach-feedback coach-error">{error}</p>}
      {message && <p role="status" className="coach-feedback coach-success">{message}</p>}
      <div id={`coach-panel-${context}`} role={context === "profile" ? "tabpanel" : undefined} tabIndex={context === "profile" ? 0 : undefined} aria-labelledby={context === "profile" ? `coach-tab-${tab}` : undefined} aria-busy={busy}>
        {tab === "guidance" && <CareerCoach guidance={profile.cv_guidance} onEdit={onEdit} onStartWriting={startWriting} />}
        {tab === "writing" && <>
          <h3>Dale más fuerza a tu experiencia</h3><p>La IA reorganiza y desarrolla tus responsabilidades, conservando los hechos que ya escribiste. Puedes añadir un resultado real para hacerlas más concretas.</p>
          <p className="coach-help">IA local, sin cobros por API. La propuesta es un borrador: revísala antes de usarla.</p>
          {!data && <p role="status">Cargando tus experiencias…</p>}
          {data && !data.experiences.length && <div className="coach-empty"><PencilLine size={28} /><h4>Empieza con una experiencia</h4><p>Puede ser un empleo, una práctica o una colaboración real. Escribe una frase sobre lo que hiciste y te ayudaremos a presentarla.</p><button type="button" className="button-primary" onClick={() => onEdit("profile-experiences")}>Añadir mi experiencia<ArrowRight size={15} /></button></div>}
          {!!data?.experiences.length && <form className="coach-form" onSubmit={(event) => { event.preventDefault(); act(async () => { const { data: response } = await api.post("/profiles/me/coach/writing/generate", { experience_index: Number(index), source_version: data.source_version, style, result }, { timeout: 100000 }); setProposalId(response.id); setMessage("Revisa la propuesta. Tu perfil sigue igual hasta que decidas usarla."); }); }}>
            <label>¿Qué experiencia quieres mejorar?<select id="coach-experience" className="field-control" value={index} onChange={(event) => { setIndex(Number(event.target.value)); setResult(""); setProposalId(""); }}>{data.experiences.map((row, i) => <option key={i} value={i}>{row.role || "Cargo por completar"} · {row.company || "Organización"}</option>)}</select></label>
            <blockquote><strong>Lo que escribiste</strong>{experience?.description || "Añade una frase sobre tus responsabilidades para poder generar una propuesta."}</blockquote>
            <fieldset className="coach-style-picker"><legend>¿Cómo quieres presentarlo?</legend>{[["paragraph", "Una descripción completa"], ["bullets", "Una lista de acciones"]].map(([value, label]) => <label key={value}><input type="radio" name="coach-writing-style" value={value} checked={style === value} onChange={() => setStyle(value)} />{label}</label>)}</fieldset>
            <details className="coach-optional"><summary>¿Quieres añadir un resultado? Es opcional</summary><label>Un resultado real que quieras incluir<textarea className="field-control" rows={2} maxLength={700} value={result} onChange={(event) => setResult(event.target.value)} placeholder="Por ejemplo: el equipo pudo consultar los pedidos en un solo lugar." /></label><p>No hace falta una cifra. También sirve una entrega o un cambio concreto.</p></details>
            <button type="submit" className="button-primary" disabled={disabled || !experience?.description?.trim()}><Sparkles size={16} />{busy ? "Preparando…" : "Generar una propuesta con IA"}</button>
            {!experience?.description?.trim() && <button className="button-secondary" type="button" onClick={() => onEdit(`experience-description-${index}`)}>Escribir mi experiencia primero</button>}
          </form>}
          {proposal && writingCard(proposal, true)}
          {!!data?.writing?.filter((row) => row.id !== proposalId).length && <section className="writing-history"><header><h4>Propuestas por experiencia</h4><p>Abre una experiencia para comparar sus versiones, de la más reciente a la anterior.</p></header>{groupWritingHistory(data.writing.filter((row) => row.id !== proposalId)).map((group) => <details className="writing-history-group" key={group.key}><summary><span><strong>{group.record.role || "Experiencia"}</strong><small>{group.record.company || "Empresa sin indicar"} · {experiencePeriod(group.record)}</small></span><b>{group.rows.length} {group.rows.length === 1 ? "versión" : "versiones"}</b><ChevronDown size={17} /></summary><div className="writing-history-versions">{group.rows.map((row, version) => <details className="writing-history-version" key={row.id}><summary><span>Versión {group.rows.length - version}<small>{row.created_at ? new Date(row.created_at).toLocaleString("es-CO", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "Fecha no disponible"}</small></span><b className={`writing-status status-${row.status}`}>{{ prepared: "Por revisar", applied: "Aplicada", undone: "Deshecha" }[row.status]}</b><ChevronDown size={15} /></summary>{writingCard(row)}</details>)}</div></details>)}</section>}
        </>}
        {tab === "radar" && <>
          <h3>Encuentra tu próximo aprendizaje</h3><p>Elige una habilidad que piden las ofertas y encuentra formación para practicarla.</p>
          {!hideFilters && <form className="coach-learning-search" onSubmit={(event) => { event.preventDefault(); act(async () => { setRadar((await api.get("/profiles/me/coach/radar", { params: filters })).data); setSkillPage(1); setSkillQuery(""); setSelectedSkill(""); }); }}>
            <div className="learning-filter-heading"><SlidersHorizontal size={18} /><strong>Personaliza tu búsqueda</strong></div>
            <div className="learning-filter-fields"><label>Cargo o profesión<input className="field-control" maxLength={160} value={filters.search} onChange={(event) => setFilters((value) => ({ ...value, search: event.target.value }))} placeholder="Ej. auxiliar contable" /></label><label>Sector<select className="field-control" value={filters.sector} onChange={(event) => setFilters((value) => ({ ...value, sector: event.target.value }))}><option value="">Todos los sectores</option>{filters.sector && !JOB_SECTORS.includes(filters.sector) && <option>{filters.sector}</option>}{JOB_SECTORS.map((sector) => <option key={sector}>{sector}</option>)}</select></label><Autocomplete label="Ciudad o ubicación" options={cities} value={filters.location} onChange={(location) => setFilters((value) => ({ ...value, location }))} placeholder="Buscar ciudad…" maxLength={120} /></div>
            <div className="learning-filter-actions"><small>Busca para actualizar las habilidades y sus cursos.</small><div><button type="button" className="learning-reset-button" disabled={busy} onClick={() => { const next = { search: "", sector: "", location: "" }; setFilters(next); act(async () => { setRadar((await api.get("/profiles/me/coach/radar", { params: next })).data); setSelectedSkill(""); }); }}><RotateCcw size={14} />Restablecer</button><button type="submit" className="button-primary" disabled={busy}><Search size={16} />Buscar habilidades</button></div></div>
          </form>}
          {!radar && <p role="status">Buscando habilidades y formación…</p>}
          {radar && <>
            <div className="coach-learning-summary"><strong>{radar.sample} ofertas consultadas</strong><span>{radar.sample ? "Elige una habilidad y abre el curso que te interese." : "Prueba otra palabra, ubicación o sector."}</span></div>
            <><div className="coach-learning-switch" aria-label="Habilidades por explorar"><button type="button" aria-pressed={radarView === "learn"} onClick={() => { setRadarView("learn"); setSkillPage(1); setSkillQuery(""); setSelectedSkill(""); }}>Solicitadas que aún no tengo <span>{learningSkills.length}</span></button><button type="button" aria-pressed={radarView === "known"} onClick={() => { setRadarView("known"); setSkillPage(1); setSkillQuery(""); setSelectedSkill(""); }}>Ya en mi perfil <span>{knownSkills.length}</span></button></div>
              {!visibleSkills.length && <div className="coach-empty"><CheckCircle2 size={28} /><h4>{radarView === "learn" ? radar.sample ? "Las habilidades mostradas ya están en tu perfil" : "No hay ofertas con estos filtros" : "Aún no tienes estas habilidades registradas"}</h4><p>{radarView === "learn" ? "Puedes profundizar en ellas desde la otra pestaña o explorar un cargo diferente." : "Si conoces alguna, puedes añadirla en Habilidades. Si quieres aprenderla, consulta los cursos sugeridos."}</p></div>}
              {!!selected && <div className="coach-learning-browser">
                <div className="coach-skill-options"><h4><span>1</span>Elige una habilidad</h4><label className="coach-skill-search"><span className="sr-only">Buscar habilidad</span><Search size={15} /><input value={skillQuery} onChange={(event) => { setSkillQuery(event.target.value); setSkillPage(1); setSelectedSkill(""); }} placeholder="Buscar entre las habilidades…" /></label><p className="coach-learning-count">{skillBrowser.total} habilidades · mayor demanda primero</p><div className="coach-skill-list">{skillBrowser.rows.map((row) => <button type="button" key={row.skill} aria-pressed={selected.skill === row.skill} onClick={() => setSelectedSkill(row.skill)}><span><strong>{skillName(row.skill)}</strong><small>{row.count} de {radar.sample} ofertas la solicitan</small></span><ArrowRight size={17} /></button>)}</div>{!skillBrowser.total && <p role="status">No hay habilidades con ese nombre.</p>}{skillBrowser.pages > 1 && <nav className="coach-skill-pagination" aria-label="Páginas de habilidades"><button className="button-secondary button-sm" disabled={skillBrowser.page === 1} onClick={() => { setSkillPage(skillBrowser.page - 1); setSelectedSkill(""); }}>Anterior</button><span>{skillBrowser.page} / {skillBrowser.pages}</span><button className="button-secondary button-sm" disabled={skillBrowser.page === skillBrowser.pages} onClick={() => { setSkillPage(skillBrowser.page + 1); setSelectedSkill(""); }}>Siguiente</button></nav>}</div>
                <section className="coach-learning-choice" aria-live="polite"><h4><span>2</span>{selected.declared ? "Sigue practicando" : "Elige cómo aprender"}</h4><h3>{skillName(selected.skill)}</h3><p>{selected.declared ? "Ya está en tu perfil. Estos recursos pueden ayudarte a profundizar." : "Que no aparezca en tu perfil no significa que no la conozcas. Puedes explorar un curso o revisar tus habilidades."}</p>
                  <div className="coach-learning-courses">{selected.courses.map((course) => <article key={course.id}><div><h5>{course.title}</h5><p>{course.provider}{course.hours ? ` · ${formatLearningHours(course.hours)} h estimadas` : ""}</p></div><Link className="coach-course-action" to={learningLink(course)}>Ver curso<ArrowUpRight size={16} /></Link></article>)}</div>
                  {!selected.courses.length && <div className="coach-empty-course"><p>Todavía no hay un curso asociado a esta habilidad.</p><Link className="coach-course-action" to={`/aprendizaje?search=${encodeURIComponent(selected.skill)}#cursos`}>Buscar formación<ArrowUpRight size={16} /></Link></div>}
                  {!selected.declared && <button type="button" className="learning-known-action" onClick={() => onEdit("profile-skills")}><span><CheckCircle2 size={20} /></span><span><strong>¿Ya sabes usar {skillName(selected.skill)}?</strong><small>Revisa tus habilidades y añádela a tu perfil</small></span><ArrowRight size={18} /></button>}
                </section>
              </div>}

            </>
            <LearningSources radar={radar} />
          </>}
        </>}
      </div>
    </div>
  </section>;
}
