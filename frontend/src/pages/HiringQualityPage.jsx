import { OfferQualityLevel } from "../components/OfferQualityLevel.jsx";
import { OfferWritingAssistant } from "../components/OfferWritingAssistant.jsx";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, CheckCircle2, Eye, Lightbulb, Plus, Save, ShieldCheck, Target, Trash2 } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { CurrencyInput } from "../components/CurrencyInput.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";
import { OfferConditions } from "../components/OfferConditions.jsx";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { CONTRACTS, LEVELS, QUALITY_STEPS, offerDraft, offerPayload } from "../utils/offerQuality.js";

export function HiringQualityPage() {
  const [params, setParams] = useSearchParams();
  const [jobs, setJobs] = useState([]), [selected, setSelected] = useState("");
  const [draft, setDraft] = useState(null), [quality, setQuality] = useState(null), [savedReport, setSavedReport] = useState(null);
  const [step, setStep] = useState(0), [search, setSearch] = useState("");
  const [error, setError] = useState(""), [previewError, setPreviewError] = useState(""), [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false), [reviewing, setReviewing] = useState(false), [loaded, setLoaded] = useState(false), [dirty, setDirty] = useState(false);
  const sequence = useRef(0), formTop = useRef(null), loadSequence = useRef(0);
  const requestedId = params.get("vacante"), requestedNew = params.get("nueva") === "1";
  useEffect(() => {
    let active = true;
    Promise.all([api.get("/organization/me"), api.get("/jobs", { params: { status: "" } })]).then(([a, b]) => {
      if (active) { setJobs(b.data.filter((job) => job.company_id === a.data.id)); setLoaded(true); }
    }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!loaded || requestedId && String(draft?.id) === requestedId) return;
    const revision = ++loadSequence.current;
    const job = requestedNew ? null : jobs.find((row) => String(row.id) === requestedId) || jobs[0];
    setSelected(job ? String(job.id) : ""); setDraft(offerDraft(job || {})); setDirty(false);
    setQuality(null); setSavedReport(null); setStep(0); setMessage(""); setError("");
    if (job) api.get(`/hiring/quality/${job.id}`).then(({ data }) => { if (revision === loadSequence.current) setSavedReport(data); }).catch((failure) => { if (revision === loadSequence.current) setError(getApiErrorMessage(failure)); });
  }, [loaded, requestedId, requestedNew]);
  useEffect(() => {
    if (!draft) return;
    let active = true;
    const revision = ++sequence.current;
    setReviewing(true); setPreviewError(""); setQuality(null);
    const timer = window.setTimeout(() => {
      api.post("/hiring/quality/preview", { ...offerPayload(draft), ...(selected ? { job_id: Number(selected) } : {}) }, { __quiet: true }).then(({ data }) => {
        if (active && revision === sequence.current) setQuality(data);
      }).catch((failure) => { if (active) { setQuality(null); setPreviewError(getApiErrorMessage(failure)); } }).finally(() => { if (active) setReviewing(false); });
    }, 450);
    return () => { active = false; window.clearTimeout(timer); };
  }, [draft, selected]);
  function update(key, value) { setDirty(true); setDraft((current) => ({ ...current, [key]: value })); }
  function detail(key, value) { update("quality_details", { ...draft.quality_details, [key]: value }); }
  function skill(index, key, value) { update("skill_requirements", draft.skill_requirements.map((row, i) => i === index ? { ...row, [key]: value } : row)); }
  function mission(index, key, value) { detail("missions", draft.quality_details.missions.map((row, i) => i === index ? { ...row, [key]: value } : row)); }
  function go(value, field = "") {
    setStep(value); formTop.current?.scrollIntoView({ block: "start", behavior: "smooth" });
    if (field) requestAnimationFrame(() => requestAnimationFrame(() => {
      const names = { title: "Nombre del cargo", salary: "Salario", contract_type: "Tipo de contrato", schedule: "Jornada y horario", location: "Modalidad", description: "Responsabilidades", requirements: "Experiencia", missions: "Resultado", process: "Entrevistas", response_days: "Respuesta", skill_requirements: "Habilidad" };
      const labels = [...(formTop.current?.querySelectorAll(".offer-editor label") || [])];
      const label = labels.find((node) => node.textContent.startsWith(names[field] || ""));
      const control = label?.querySelector("input, select, textarea");
      control?.focus({ preventScroll: true }); label?.scrollIntoView({ block: "center", behavior: "smooth" });
    }));
  }
  async function save(publish = false, asDraft = false) {
    setBusy(true); setError(""); setMessage("");
    try {
      const payload = { ...offerPayload(draft), status: asDraft ? "draft" : publish ? "active" : draft.status === "active" ? "active" : "draft" };
      const { data } = selected ? await api.patch(`/jobs/${selected}`, payload) : await api.post("/jobs", payload);
      setJobs((current) => [data, ...current.filter((job) => job.id !== data.id)]);
      setSelected(String(data.id)); setDraft(offerDraft(data)); setDirty(false); setParams({ vacante: String(data.id) }, { replace: true });
      setSavedReport((await api.get(`/hiring/quality/${data.id}`)).data);
      setMessage(data.status === "draft" && publish ? "Guardada como borrador. Completa la verificación de la empresa para publicar." : publish ? "Oferta publicada. Las condiciones y el proceso ya están visibles para los candidatos." : "Cambios guardados. Puedes continuar cuando quieras.");
    } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  const d = draft?.quality_details;
  const canPublish = quality?.can_publish && !reviewing && !previewError;
  return <div className="offer-studio space-y-5">
    <PageHeader kicker="Consultor de ofertas" title="Una buena contratación empieza aquí" description="Define condiciones claras, resultados y un proceso que puedas cumplir. Te acompañamos mientras construyes la oferta." actions={<Link className="button-secondary" to="/empresa/vacantes"><ArrowLeft size={16} />Mis vacantes</Link>} />
    <section className="surface-card offer-picker"><Field label="Trabaja en una oferta"><input className="field-control" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar por cargo" /></Field><Field label="Vacante"><select className="field-control" value={selected} disabled={busy || dirty} onChange={(event) => setParams(event.target.value ? { vacante: event.target.value } : { nueva: "1" })}><option value="">Nueva oferta</option>{jobs.filter((job) => String(job.id) === selected || job.title.toLowerCase().includes(search.toLowerCase())).map((job) => <option key={job.id} value={job.id}>{job.title} · {job.status === "active" ? "Activa" : job.status === "draft" ? "Borrador" : "Cerrada / pausada"}</option>)}</select></Field><button className="button-secondary" type="button" disabled={busy || dirty} onClick={() => { if (requestedNew) { setSelected(""); setDraft(offerDraft()); setSavedReport(null); setStep(0); } else setParams({ nueva: "1" }); }}><Plus size={17} />Nueva oferta</button>{dirty && <p className="col-span-full text-xs text-[var(--muted)]">Tienes cambios sin guardar. <button type="button" className="offer-text-button" onClick={() => { setDraft(offerDraft(jobs.find((row) => String(row.id) === selected) || {})); setDirty(false); }}>Descartar cambios</button></p>}</section>
    {error && <p role="alert" className="offer-alert error">{error}</p>}{message && <p role="status" className="offer-alert success"><CheckCircle2 size={18} />{message}</p>}
    {draft && <>
      <nav className="offer-steps" aria-label="Pasos para preparar la oferta">{QUALITY_STEPS.map((label, index) => {
        const checks = quality?.checks.filter((row) => row.step === index) || [];
        const complete = checks.length > 0 && checks.every((row) => row.passed);
        return <button key={label} type="button" aria-current={step === index ? "step" : undefined} className={step === index ? "active" : ""} onClick={() => go(index)}><span>{complete ? <Check size={14} /> : index + 1}</span><strong>{label}</strong></button>;
      })}</nav>
      <div className="offer-mobile-score"><div><strong>{quality?.score ?? "—"}<small>/100</small></strong><p>{reviewing ? "Revisando…" : quality?.can_publish ? "Lista para publicar" : "Oferta en preparación"}</p></div><button type="button" onClick={() => go(quality?.next_actions[0]?.step ?? 4)}>{quality?.next_actions.length ? "Siguiente mejora" : "Revisar oferta"}<ArrowRight size={15} /></button></div>
      <div className="offer-workspace" ref={formTop}>
        <form className="surface-card offer-editor" onSubmit={(event) => { event.preventDefault(); if (step < 4) go(step + 1); else save(false); }}>
          <header className="offer-step-header"><p className="section-kicker">Paso {step + 1} de 5</p><h2>{QUALITY_STEPS[step]}</h2><p>{["Lo que la persona necesita saber antes de postularse.", "Explica qué hará, con quién y qué resultados esperas.", "Pide lo necesario y deja espacio para aprender.", "Acuerda los pasos y plazos con tu equipo.", "Así verá el candidato las condiciones que estás ofreciendo."][step]}</p></header>
          {step === 0 && <div className="offer-fields">
            <Field label="Nombre del cargo" wide><input className="field-control" maxLength={180} value={draft.title} onChange={(event) => update("title", event.target.value)} placeholder="Ej. Analista de datos" /></Field>
            <Field label="Salario fijo mínimo mensual (COP)"><CurrencyInput value={draft.salary} onChange={(value) => update("salary", value)} placeholder="3.500.000" /></Field>
            <Field label="Salario fijo máximo (opcional)"><CurrencyInput value={d.salary_max} onChange={(value) => detail("salary_max", value)} placeholder="4.500.000" /></Field>
            <Field label="Comisiones o pagos variables (opcional)" wide help="Se comparará el mínimo fijo con las preferencias del candidato."><input className="field-control" maxLength={500} value={d.variable_pay} onChange={(event) => detail("variable_pay", event.target.value)} placeholder="Explica la fórmula y sus condiciones" /></Field>
            <Field label="Tipo de contrato"><select className="field-control" value={d.contract_type} onChange={(event) => detail("contract_type", event.target.value)}><option value="">Selecciona un contrato</option>{Object.entries(CONTRACTS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field>
            <Field label="Dedicación"><select className="field-control" value={draft.employment_type} onChange={(event) => update("employment_type", event.target.value)}><option value="full_time">Tiempo completo</option><option value="part_time">Medio tiempo</option><option value="internship">Prácticas</option><option value="temporary">Temporal</option><option value="contract">Por contrato</option></select></Field>
            <Field label="Modalidad"><select className="field-control" value={draft.modality} onChange={(event) => update("modality", event.target.value)}><option value="remote">Remota</option><option value="hybrid">Híbrida</option><option value="onsite">Presencial</option></select></Field>
            <Field label={draft.modality === "remote" ? "Territorio permitido para trabajar" : "Ciudad de trabajo"}><input className="field-control" maxLength={120} value={draft.location || ""} onChange={(event) => update("location", event.target.value)} placeholder={draft.modality === "remote" ? "Ej. Colombia" : "Ej. Bogotá"} /></Field>
            <Field label="Jornada y horario" wide><input className="field-control" maxLength={300} value={d.schedule} onChange={(event) => detail("schedule", event.target.value)} placeholder="Lunes a viernes, 8:00 a 17:00, con una hora de descanso" /></Field>
            <Field label="Sector"><select className="field-control" value={draft.sector} onChange={(event) => update("sector", event.target.value)}>{JOB_SECTORS.map((sector) => <option key={sector}>{sector}</option>)}</select></Field>
            <Field label="Beneficios (uno por línea)"><textarea className="field-control" rows={3} value={(draft.benefits || []).join("\n")} onChange={(event) => update("benefits", event.target.value.split("\n"))} /></Field>
          </div>}
          {step === 1 && <div className="space-y-5">
            <Field label="Responsabilidades y contexto" help="Describe acciones, entregables, equipo y recursos disponibles."><textarea className="field-control min-h-40" maxLength={20000} value={draft.description} onChange={(event) => update("description", event.target.value)} placeholder="Analizará reportes de ventas con el equipo comercial, documentará diferencias y preparará un tablero semanal para tomar decisiones." /></Field>
            <div className="offer-tip"><Lightbulb size={20} /><p>Define <strong>qué se entregará, cómo se revisará y cuándo</strong>. La evaluación puede ser una revisión documentada; adapta el plazo a la duración del cargo.</p></div>
            <h3 className="font-bold">Misiones del cargo <span className="text-xs text-[var(--muted)]">{d.missions.length} de 5</span></h3>
            {!d.missions.length && <div className="offer-empty"><Target size={28} /><h3>¿Qué debería lograr al incorporarse?</h3><p>Define una primera entrega concreta y cómo la evaluará el equipo.</p></div>}
            {d.missions.map((row, index) => <fieldset className="offer-mission" key={index}><legend>Misión {index + 1}</legend><Field label="Resultado esperado"><textarea className="field-control" rows={2} maxLength={500} value={row.outcome} onChange={(event) => mission(index, "outcome", event.target.value)} placeholder="Preparar un tablero de ventas con fuentes documentadas" /></Field><Field label="Cómo se evaluará"><input className="field-control" maxLength={300} value={row.measure} onChange={(event) => mission(index, "measure", event.target.value)} placeholder="Revisión con el equipo y conciliación contra el reporte de origen" /></Field><div className="offer-fields"><Field label="Plazo desde el ingreso (días)"><input className="field-control" type="number" min={1} max={365} value={row.days} onChange={(event) => mission(index, "days", event.target.value)} /></Field><Field label="Habilidad relacionada (opcional)"><input className="field-control" maxLength={100} value={row.skill} onChange={(event) => mission(index, "skill", event.target.value)} /></Field></div><button type="button" className="offer-text-button" onClick={() => detail("missions", d.missions.filter((_, i) => i !== index))}><Trash2 size={14} />Quitar misión</button></fieldset>)}
            <button type="button" className="button-secondary" disabled={d.missions.length >= 5} onClick={() => detail("missions", [...d.missions, { outcome: "", measure: "", days: 90, skill: "" }])}><Plus size={16} />Añadir misión</button>
          </div>}
          {step === 2 && <div className="space-y-5">
            <div className="offer-fields"><Field label="Nivel del cargo"><select className="field-control" value={d.seniority} onChange={(event) => detail("seniority", event.target.value)}><option value="">Selecciona el nivel</option>{Object.entries(LEVELS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></Field><Field label="Experiencia mínima (años)" help="Puedes indicar 0 y aceptar proyectos o formación."><input className="field-control" type="number" min={0} max={50} value={d.experience_years ?? ""} onChange={(event) => detail("experience_years", event.target.value === "" ? null : Number(event.target.value))} /></Field></div>
            <Field label="Conocimientos y evidencia aceptada"><textarea className="field-control min-h-28" maxLength={20000} value={draft.requirements} onChange={(event) => update("requirements", event.target.value)} placeholder="Fundamentos de SQL. Aceptamos proyectos de formación o ejemplos de trabajo para demostrar estas habilidades." /></Field>
            <div><h3 className="font-bold">Habilidades para la compatibilidad</h3><p className="mt-1 text-sm text-[var(--muted)]">Esencial: necesaria al ingresar. Deseable: suma afinidad. Peso: importancia de 1 a 5.</p></div>
            {draft.skill_requirements.map((row, index) => <div className="offer-skill" key={index}><Field label={`Habilidad ${index + 1}`}><input className="field-control" maxLength={100} value={row.skill} onChange={(event) => skill(index, "skill", event.target.value)} /></Field><Field label="Prioridad"><select className="field-control" value={row.essential ? "essential" : "desirable"} onChange={(event) => skill(index, "essential", event.target.value === "essential")}><option value="essential">Esencial</option><option value="desirable">Deseable</option></select></Field><Field label="Peso"><select className="field-control" value={row.weight} onChange={(event) => skill(index, "weight", Number(event.target.value))}>{[1, 2, 3, 4, 5].map((value) => <option key={value}>{value}</option>)}</select></Field><button type="button" aria-label={`Quitar habilidad ${index + 1}`} className="button-secondary" onClick={() => update("skill_requirements", draft.skill_requirements.filter((_, i) => i !== index))}><Trash2 size={16} /></button></div>)}
            <button type="button" className="button-secondary" disabled={draft.skill_requirements.length >= 10} onClick={() => update("skill_requirements", [...draft.skill_requirements, { skill: "", essential: true, weight: 3 }])}><Plus size={16} />Añadir habilidad</button>
            <Field label="Habilidades que la empresa enseñará (separadas por comas)" help="Se muestran como oportunidades de aprendizaje."><input className="field-control" value={d.learnable_skills.join(",")} onChange={(event) => detail("learnable_skills", event.target.value.split(","))} /></Field>
            <details className="offer-advanced"><summary>Idiomas y selección ciega</summary><div className="space-y-4 pt-4"><LanguagesEditor value={draft.languages} required onChange={(value) => update("languages", value)} /><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={draft.blind_hiring} disabled={!!selected} onChange={(event) => update("blind_hiring", event.target.checked)} />Proteger la identidad durante las etapas iniciales</label><p className="text-xs text-[var(--muted)]">Preguntas de selección y requisitos académicos: disponibles en Mis vacantes después de guardar.</p></div></details>
          </div>}
          {step === 3 && <div className="space-y-5"><div className="offer-fields"><Field label="Entrevistas previstas"><input className="field-control" type="number" min={0} max={10} value={d.interview_count ?? ""} onChange={(event) => detail("interview_count", event.target.value === "" ? null : Number(event.target.value))} /></Field><Field label="Duración total estimada (días)"><input className="field-control" type="number" min={1} max={180} value={d.process_days ?? ""} onChange={(event) => detail("process_days", event.target.value === "" ? null : Number(event.target.value))} /></Field><Field label="Respuesta por avance (días)" help="Este compromiso se utiliza en el seguimiento del proceso."><input className="field-control" type="number" min={1} max={30} value={draft.response_days} onChange={(event) => update("response_days", event.target.value)} /></Field></div><div className="offer-tip"><Lightbulb size={20} /><p>Acuerda estos plazos con el equipo. El candidato verá las entrevistas previstas y el tiempo estimado desde su postulación.</p></div><h3 className="font-bold">Etapas visibles del proceso</h3><ol className="offer-pipeline">{(draft.pipeline_stages || [{ id: "submitted", title: "Recibida" }, { id: "reviewing", title: "En revisión" }, { id: "interview", title: "Entrevista" }, { id: "hired", title: "Contratación" }, { id: "rejected", title: "No seleccionada" }]).map((row, index) => <li key={row.id}><span>{index + 1}</span><div><strong>{row.title}</strong><small>Etapa del tablero de candidatos</small></div></li>)}</ol><p className="text-xs text-[var(--muted)]">Puedes personalizar las etapas en Postulaciones después de guardar.</p></div>}
          {step === 4 && <div className="space-y-5"><div className="offer-candidate-heading"><p className="section-kicker">Vista del candidato</p><h3>{draft.title || "Nombre del cargo"}</h3><p>{draft.sector}</p></div><OfferConditions job={{ ...draft, quality_summary: quality && !reviewing ? { score: quality.score, level: quality.level } : null }} preview /><div><h3 className="font-bold">Responsabilidades</h3><p className="mt-2 whitespace-pre-line text-sm text-[var(--muted)]">{draft.description || "Completa las responsabilidades."}</p></div><div><h3 className="font-bold">Requisitos y evidencia</h3><p className="mt-2 whitespace-pre-line text-sm text-[var(--muted)]">{draft.requirements || "Completa los requisitos."}</p></div><div className="offer-tip"><ShieldCheck size={20} /><p>La calidad mide la información de la oferta. La compatibilidad se calcula con cada perfil y la confianza refleja el comportamiento de la empresa.</p></div>{!!selected && <Link className="button-secondary" to={`/vacantes/${selected}`}><Eye size={16} />Abrir detalle guardado</Link>}</div>}
          <footer className="offer-editor-footer"><button className="button-secondary" type="button" disabled={step === 0 || busy} onClick={() => go(step - 1)}><ArrowLeft size={16} />Anterior</button>{step < 4 ? <button className="button-primary" type="submit">Continuar<ArrowRight size={16} /></button> : <button className="button-primary" type="button" disabled={busy || !canPublish || ["filled", "closed"].includes(draft.status)} onClick={() => save(true)}><CheckCircle2 size={16} />{draft.status === "active" ? "Guardar oferta publicada" : "Publicar oferta"}</button>}</footer>
        </form>
        <aside className="offer-advisor">
          <section className="surface-card offer-score"><div className="flex items-center justify-between gap-2"><span className="section-kicker">Revisión en vivo</span><span className="offer-level">{quality?.rating ? `${quality.rating.label} · Nivel ${quality.rating.code}` : "Sin evaluar"}</span></div><div className="offer-score-number"><strong>{quality?.score ?? "—"}</strong><span>/ 100</span></div><progress aria-label="Puntuación de la oferta" value={quality?.score ?? 0} max={100} /><OfferQualityLevel quality={quality} /><p role="status" className="mt-3 text-sm font-semibold">{reviewing ? "Revisando tus cambios…" : quality?.readiness || (previewError ? "Corrige el campo indicado para continuar la revisión" : "Preparando revisión…")}</p><p className="mt-2 text-xs text-[var(--muted)]">30 condiciones · 25 responsabilidades · 20 requisitos · 15 proceso · 10 lenguaje</p>{previewError && <p role="alert" className="mt-3 text-xs text-[var(--error)]">{previewError}</p>}<button className="button-secondary mt-5 w-full" type="button" disabled={busy || !!previewError || reviewing || draft.title.trim().length < 2 || draft.description.trim().length < 10 || draft.requirements.trim().length < 10 || ["filled", "closed"].includes(draft.status)} onClick={() => save(false)}><Save size={16} />{busy ? "Guardando…" : draft.status === "active" ? "Guardar cambios" : "Guardar borrador"}</button><p className="mt-2 text-xs text-[var(--muted)]">{draft.status === "active" ? "Los cambios se reflejarán en la oferta publicada." : "El borrador solo es visible para tu empresa."}</p>{draft.status === "active" && !canPublish && <button className="offer-text-button mt-3" type="button" disabled={busy} onClick={() => save(false, true)}>Guardar borrador y retirar publicación</button>}</section>
          {quality && <section className="surface-card offer-checklist"><h3 className="font-bold">Tu siguiente mejora</h3>{quality.next_actions.length ? quality.next_actions.slice(0, 3).map((row) => <button type="button" key={row.key} onClick={() => go(row.step, row.key || row.field)}><span>{row.required ? "Obligatorio" : "Recomendación"} · {row.weight} puntos</span><strong>{row.label}<ArrowRight size={14} /></strong><small>{row.action}</small></button>) : <div className="offer-ready"><CheckCircle2 size={24} /><p>La oferta cumple los criterios de esta revisión.</p></div>}<details className="mt-4"><summary>Ver todos los criterios</summary><div className="mt-3 space-y-3">{quality.checks.map((row) => <button key={row.key} className="offer-criterion" type="button" onClick={() => go(row.step, row.key || row.field)}><span>{row.passed ? "✓" : "○"} {row.label}</span><strong>{row.weight ? `${row.passed ? row.weight : 0}/${row.weight}` : row.passed ? "Completo" : "Requerido"}</strong></button>)}</div></details></section>}
          {!!quality?.issues.length && <section className="surface-card offer-coach"><h3><Lightbulb size={18} />Asistente de claridad</h3>{quality.issues.map((row) => <button type="button" key={row.code} onClick={() => go(row.step, row.key || row.field)}><span>{row.severity === "critical" ? "Revisa antes de publicar" : "Sugerencia"}</span><strong>{row.message}</strong>{row.suggestion && <small>{row.suggestion}</small>}</button>)}</section>}
          {quality && <details className="surface-card offer-reference"><summary>Referencia salarial local</summary><p className="mt-3 text-sm">{quality.salary_reference.median ? `$${quality.salary_reference.median.toLocaleString("es-CO")} COP · ${quality.salary_reference.sample_size} empresas comparables` : `Muestra insuficiente: ${quality.salary_reference.sample_size} de 5 empresas comparables.`}</p><p className="mt-2 text-xs text-[var(--muted)]">{quality.salary_reference.notice}</p></details>}
        </aside>
      </div>
      <OfferWritingAssistant key={selected || "new"} draft={draft} disabled={busy} onApply={update} onStep={go} />
      {savedReport?.feedback && <section className="surface-card offer-diagnostics"><div><p className="section-kicker">Después de publicar</p><h2>Lo que dicen los candidatos</h2><p className="text-sm text-[var(--muted)]">Versión {savedReport.revision} · {savedReport.feedback.sample_size} opiniones voluntarias{dirty ? " · Guarda para actualizar la versión" : ""}</p></div>{savedReport.feedback.available ? <div className="offer-feedback-grid">{savedReport.feedback.reasons.filter((row) => row.count > 0).map((row) => <article key={row.key}><strong>{row.count}</strong><h3>{row.label}</h3><p>{row.action}</p></article>)}</div> : <p className="offer-tip">El diagnóstico aparecerá cuando esta versión reúna cinco opiniones. Puedes probarlo con la oferta de ejemplo que incluye comentarios.</p>}<p className="text-xs text-[var(--muted)]">{savedReport.feedback.notice}</p></section>}
    </>}
  </div>;
}

function Field({ label, help, wide, children }) {
  return <label className={`offer-field ${wide ? "wide" : ""}`}><span>{label}</span>{children}{help && <small>{help}</small>}</label>;
}
