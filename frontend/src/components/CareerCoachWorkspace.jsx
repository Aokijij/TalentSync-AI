import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Download, FileSearch, PencilLine, Target, TrendingUp, Undo2 } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { buildStarDraft } from "../utils/careerCoach.js";
import "../styles/career-coach.css";

const tabs = [["writing", "Redacción", PencilLine], ["vacancy", "Por vacante", Target], ["reading", "Lectura del PDF", FileSearch], ["radar", "Demanda y formación", TrendingUp]];

export function CareerCoachWorkspace({ profile, editing, launch, onProfileChanged }) {
  const [opened, setOpened] = useState(false), [tab, setTab] = useState("writing");
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(""), [message, setMessage] = useState("");
  const [index, setIndex] = useState(0), [facts, setFacts] = useState({ situation: "", task: "", action: "", result: "" }), [texts, setTexts] = useState({});
  const [search, setSearch] = useState(""), [jobs, setJobs] = useState([]), [jobId, setJobId] = useState("");
  const [intros, setIntros] = useState({}), [checks, setChecks] = useState({});
  const [reading, setReading] = useState(null), [pdf, setPdf] = useState("");
  const [filters, setFilters] = useState({ search: "", sector: profile.preferred_sector || "", location: "" }), [radar, setRadar] = useState(null);
  const draft = buildStarDraft(facts);
  async function load() { setData((await api.get("/profiles/me/coach")).data); }
  useEffect(() => { if (!editing) load().catch((failure) => setError(getApiErrorMessage(failure))); }, [editing, profile.experiences, profile.skills]);
  useEffect(() => { if (launch) { setOpened(true); setTab(launch.tab); if (launch.index != null) setIndex(launch.index); if (launch.jobId) setJobId(String(launch.jobId)); document.getElementById("career-coach-workspace")?.scrollIntoView({ block: "start", behavior: "smooth" }); } }, [launch]);
  useEffect(() => {
    if (!opened || tab !== "reading") return;
    let active = true, objectUrl = "";
    setError(""); setReading(null); setPdf("");
    Promise.all([api.get("/profiles/me/coach/reading"), api.get("/profiles/me/coach/pdf", { responseType: "blob" })]).then(([text, file]) => {
      objectUrl = URL.createObjectURL(file.data);
      if (active) { setReading(text.data); setPdf(objectUrl); } else URL.revokeObjectURL(objectUrl);
    }).catch((failure) => { if (active) setError(getApiErrorMessage(failure, "Sube un PDF con texto para comparar su lectura.")); });
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [opened, tab, profile.cv_uploaded_at]);
  async function act(action, refreshProfile = false) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); await load(); if (refreshProfile) await onProfileChanged(); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function download(draftId, applicationId) {
    try {
      const { data: file } = await api.get("/profiles/me/coach/export", { params: applicationId ? { application_id: applicationId } : draftId ? { draft_id: draftId } : {}, responseType: "blob" });
      const url = URL.createObjectURL(file), anchor = document.createElement("a"); anchor.href = url; anchor.download = "perfil-simple.pdf"; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (failure) { setError(getApiErrorMessage(failure, "No fue posible descargar el perfil.")); }
  }
  const disabled = editing || busy;
  return <details id="career-coach-workspace" className="coach-workspace print-hidden" open={opened} onToggle={(event) => setOpened(event.currentTarget.open)}>
    <summary><span><strong>Coach de Carrera</strong><small>Prepara tu perfil y tu próxima postulación</small></span><BookOpen size={22} /></summary>
    <div className="coach-workspace-body">
      <div className="coach-tabs" role="tablist" aria-label="Herramientas de carrera">{tabs.map(([key, label, Icon]) => <button id={`coach-tab-${key}`} key={key} type="button" role="tab" aria-selected={tab === key} aria-controls="coach-panel" onClick={() => { setTab(key); setError(""); setMessage(""); }}><Icon size={16} />{label}</button>)}</div>
      {editing && <p role="status" className="coach-notice">Guarda las ediciones del perfil para preparar o aplicar propuestas sobre esa versión.</p>}
      {error && <p role="alert" className="text-[var(--error)]">{error}</p>}{message && <p role="status" className="text-[var(--success)]">{message}</p>}
      <div id="coach-panel" role="tabpanel" aria-labelledby={`coach-tab-${tab}`}>
        {tab === "writing" && <>
          <h3>De una responsabilidad a un aporte concreto</h3><p>Describe hechos de tu experiencia. Revisa el antes y el después, edita la propuesta y decide si quieres aplicarla. Puedes deshacerla mientras esa experiencia no haya cambiado.</p>
          {data?.experiences?.length ? <form className="coach-form" onSubmit={(event) => { event.preventDefault(); act(async () => { await api.post("/profiles/me/coach/writing", { experience_index: Number(index), source_version: data.source_version, facts }); setMessage("Propuesta preparada. Revisa el antes y después antes de aplicarla."); }); }}>
            <label>Experiencia<select value={index} onChange={(event) => { setIndex(Number(event.target.value)); setFacts({ situation: "", task: "", action: "", result: "" }); }}>{data.experiences.map((row, i) => <option key={i} value={i}>{row.role || "Cargo por completar"} · {row.company || "Organización"}</option>)}</select></label>
            <div className="coach-columns">{[["situation", "Situación", "¿Qué necesidad o problema había?"], ["task", "Objetivo", "¿Qué tenías que conseguir?"], ["action", "Tu acción", "¿Qué hiciste tú? ¿Con qué herramienta o método?"], ["result", "Resultado real", "¿Qué entregaste o qué cambió? Puede ser un resultado sin cifras."]].map(([key, label, hint]) => <label key={key}>{label}<textarea required rows={3} maxLength={700} placeholder={hint} value={facts[key]} onChange={(event) => setFacts((value) => ({ ...value, [key]: event.target.value }))} /></label>)}</div>
            {draft && <blockquote><strong>Vista previa</strong>{draft}</blockquote>}<button type="submit" className="button-primary button-sm" disabled={disabled || !draft}>Preparar propuesta</button>
          </form> : <p className="coach-notice">Añade una experiencia real para trabajar su redacción. Si buscas tu primer empleo, puedes mostrar proyectos o prácticas en tus evidencias.</p>}
          <h4>Historial de propuestas · últimas 20</h4>{!data?.writing?.length && <p>Aún no has preparado propuestas.</p>}
          {data?.writing?.map((row) => <details className="coach-record" key={row.id}><summary>{row.record.role || "Experiencia"} · {{ prepared: "Por revisar", applied: "Aplicada", undone: "Deshecha" }[row.status]}</summary><div className="coach-columns"><div><strong>Antes</strong><blockquote>{row.before || "Sin descripción"}</blockquote></div><label>Propuesta editable<textarea rows={5} maxLength={3000} disabled={row.status !== "prepared"} value={texts[row.id] ?? row.after} onChange={(event) => setTexts((value) => ({ ...value, [row.id]: event.target.value }))} /></label></div>
            {row.status === "prepared" && <button className="button-primary button-sm" type="button" disabled={disabled || !(texts[row.id] ?? row.after).trim()} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "apply", text: texts[row.id] ?? row.after }); setMessage("Descripción aplicada a tu perfil."); }, true)}>Aplicar al perfil</button>}
            {row.status === "applied" && <button className="button-secondary button-sm" type="button" disabled={disabled} onClick={() => act(async () => { await api.put(`/profiles/me/coach/writing/${row.id}`, { action: "undo" }); setMessage("Se restauró la descripción anterior."); }, true)}><Undo2 size={14} />Deshacer</button>}
          </details>)}
        </>}
        {tab === "vacancy" && <>
          <h3>Una versión para cada oportunidad</h3><p>La presentación usa habilidades ya declaradas y conserva tus cargos, empresas y fechas. Las preguntas señalan información que falta; no la añaden como conocimiento. Cada versión se guarda separada de tu perfil principal.</p>
          <form className="coach-search" onSubmit={(event) => { event.preventDefault(); act(async () => setJobs((await api.get("/profiles/me/coach/jobs", { params: { search } })).data.items)); }}><label>Buscar vacante<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cargo o palabras del título" maxLength={160} /></label><button className="button-secondary button-sm" disabled={busy}>Buscar</button></form>
          <div className="coach-search"><label>Vacante disponible<select value={jobId} onChange={(event) => setJobId(event.target.value)}><option value="">Selecciona una vacante</option>{jobId && !jobs.some((job) => String(job.id) === jobId) && <option value={jobId}>Vacante seleccionada · {jobId}</option>}{jobs.map((job) => <option key={job.id} value={job.id}>{job.title} · {job.location || "Ubicación por confirmar"}</option>)}</select></label><button type="button" className="button-primary button-sm" disabled={disabled || !jobId} onClick={() => act(async () => { await api.post("/profiles/me/coach/drafts", { job_id: Number(jobId) }); setMessage("Versión preparada: revísala y confirma que refleja tu experiencia."); })}>Preparar versión</button></div>
          <h4>Mis versiones · últimas 20</h4>{!data?.drafts?.length && <p>Aún no tienes versiones guardadas.</p>}
          {!!data?.submitted?.length && <section><h4>Versiones ya enviadas · últimas 20</h4>{data.submitted.map((row) => <details className="coach-record" key={row.application_id}><summary>{row.job_title} · enviada {new Date(row.created_at).toLocaleDateString("es-CO")}</summary><blockquote>{row.intro}</blockquote><p>Esta copia conserva la información enviada aunque cambie tu perfil o tus borradores.</p><button type="button" className="button-secondary button-sm" onClick={() => download(null, row.application_id)}><Download size={14} />Descargar versión enviada</button></details>)}</section>}
          {data?.drafts?.map((row) => <details className="coach-record" key={row.id}><summary>{row.job_title} · {row.confirmed ? "Revisada" : "Por revisar"}</summary><p>Habilidades declaradas relacionadas: {row.supported_skills.join(", ") || "Sin coincidencias explícitas"}</p><label>Presentación<textarea rows={4} maxLength={2000} value={intros[row.id] ?? row.intro} onChange={(event) => { setIntros((value) => ({ ...value, [row.id]: event.target.value })); setChecks((value) => ({ ...value, [row.id]: false })); }} /></label>{!!row.questions.length && <details><summary>Preguntas para revisar brechas</summary>{row.questions.map((question) => <p key={question}>{question}</p>)}<Link to="/aprendizaje#cursos">Explorar formación</Link></details>}<label className="coach-check"><input type="checkbox" checked={checks[row.id] ?? row.confirmed} onChange={(event) => setChecks((value) => ({ ...value, [row.id]: event.target.checked }))} />Confirmo que esta presentación refleja mi experiencia real.</label><div className="coach-actions"><button type="button" className="button-primary button-sm" disabled={disabled || !(checks[row.id] ?? row.confirmed)} onClick={() => act(async () => { const { data: saved } = await api.put(`/profiles/me/coach/drafts/${row.id}`, { revision: row.revision, intro: intros[row.id] ?? row.intro, confirmed: true }); setIntros((value) => ({ ...value, [row.id]: saved.intro })); setMessage("Versión revisada y guardada. Puedes seleccionarla al postularte."); })}>Guardar versión revisada</button><button type="button" className="button-secondary button-sm" disabled={(intros[row.id] ?? row.intro) !== row.intro} onClick={() => download(row.id)}><Download size={14} />PDF de esta versión</button><Link className="button-secondary button-sm" to={`/vacantes/${row.job_id}`}>Ir a la vacante</Link></div></details>)}
        </>}
        {tab === "reading" && <>
          <h3>Así se lee tu PDF en TalentSync</h3><p>Compara el documento con el texto extraído y revisa si hay columnas mezcladas o datos que faltan.</p>
          {reading && <><p>{reading.method} · {reading.pages} páginas{reading.truncated ? " · Texto acotado para esta vista" : ""}</p><div className="coach-pdf-columns">{pdf && <iframe title="Tu PDF original" src={pdf} />}<section><h4>Texto extraído</h4><pre>{reading.text || "No se encontró texto seleccionable. Se necesita una versión con texto u OCR."}</pre></section></div><p className="coach-notice">{reading.note}</p></>}
          <button className="button-secondary button-sm" type="button" onClick={() => download()}><Download size={15} />Descargar perfil simple de una columna</button>
        </>}
        {tab === "radar" && <>
          <h3>Qué habilidades piden las ofertas disponibles</h3><p>Elige los cargos y la ubicación que te interesan. La comparación usa vacantes activas; no compara ni publica datos de otros candidatos.</p>
          <form className="coach-search" onSubmit={(event) => { event.preventDefault(); act(async () => setRadar((await api.get("/profiles/me/coach/radar", { params: filters })).data)); }}>{[["search", "Cargo"], ["sector", "Sector"], ["location", "Ubicación"]].map(([key, label]) => <label key={key}>{label}<input maxLength={160} value={filters[key]} onChange={(event) => setFilters((value) => ({ ...value, [key]: event.target.value }))} placeholder={key === "search" ? profile.profession || "Todos los cargos" : "Cualquiera"} /></label>)}<button className="button-primary button-sm" disabled={busy}>Consultar demanda</button></form>
          {radar && <><p><strong>{radar.sample} ofertas según estos filtros</strong> · Desde {radar.since} · Consulta {new Date(radar.as_of).toLocaleDateString("es-CO")}</p><p className="coach-notice">{radar.note}{radar.small_sample ? " La muestra es pequeña; mostramos recuentos sin porcentajes." : ""}</p><p>Fuentes: {Object.entries(radar.sources).map(([name, count]) => `${name} (${count})`).join(", ") || "Sin ofertas"}</p><div className="coach-demand-grid">{radar.skills.map((row) => <article key={row.skill}><h4>{row.skill}</h4><p>{row.count} de {radar.sample} ofertas{row.percentage == null ? "" : ` · ${row.percentage}%`}</p><p>{row.declared ? "Ya está declarada en tu perfil" : "Revisa si la conoces o quieres aprenderla"}</p>{row.courses.map((course) => <Link key={course.id} to={`/aprendizaje?search=${encodeURIComponent(course.title)}#cursos`}>{course.title} · {course.provider}</Link>)}{!row.courses.length && <p>Sin formación asociada en el catálogo actual.</p>}</article>)}</div>{!radar.sample && <p>No hay ofertas con estos criterios. Prueba otro cargo, sector o ubicación.</p>}<details><summary>Ver ofertas de la muestra · hasta 10</summary>{radar.jobs.map((job) => <p key={job.id}><Link to={`/vacantes/${job.id}`}>{job.title} · {job.location}</Link></p>)}</details></>}
        </>}
      </div>
    </div>
  </details>;
}
