import { CourseBatchImport } from "../components/CourseBatchImport.jsx";
import { AdminLearningLibrary } from "../components/AdminLearningLibrary.jsx";
import { LearningConnectors } from "../components/LearningConnectors.jsx";
import { ArrowRight, ArrowLeft } from "lucide-react";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { certificateCosts, courseModalities, enrollmentStatuses, learningLevels } from "../utils/learningPresentation.js";

export function LearningCatalogPage() {
  const { confirm } = useFeedback();
  const [step, setStep] = useState(0), [preview, setPreview] = useState({});
  function advance(event) { event.preventDefault(); const form = event.currentTarget.closest("form"); const fields = [...form.querySelectorAll(`fieldset[data-step="${step}"] input, fieldset[data-step="${step}"] textarea, fieldset[data-step="${step}"] select`)]; if (fields.some((field) => !field.reportValidity())) return; setPreview(Object.fromEntries(new FormData(form))); setStep(step + 1); }
  const [view, setView] = useState("library");
  const [formOpen, setFormOpen] = useState(false);
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (formOpen) document.getElementById("catalog-editor")?.scrollIntoView({ block: "start", behavior: "smooth" }); }, [formOpen, step]);
  useEffect(() => { api.get("/admin/learning/resources").then(({ data }) => setRows(data)).catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  const listedRows = rows.filter((row) => row.version || row.active !== false);
  async function act(action) {
    setBusy(true); setError(""); setMessage("");
    try { setRows(await action()); setMessage("Catálogo guardado"); setEditing(null); setFormOpen(false); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function save(event) {
    event.preventDefault(); if (step < 2) { advance(event); return; } const form = event.currentTarget; const values = new FormData(form);
    const content = { title: values.get("title"), provider: values.get("provider"), url: values.get("url"), instructions: values.get("instructions"),
      category: values.get("category"), kind: values.get("kind"), hours: Number(values.get("hours")), skills: values.get("skills").split(",").map((item) => item.trim()).filter(Boolean),
      cost: values.get("cost"), sponsored: values.has("sponsored"), affiliate: values.has("affiliate"), disclosure: values.get("disclosure"), active: values.has("active") };
    const detailKeys = ["prerequisites", "access_notes", "certificate_notes", "portfolio_idea", "duration_notes"];
    if (editing?.details || values.get("detail_syllabus")?.trim() || values.get("detail_languages")?.trim() || detailKeys.some((key) => values.get(`detail_${key}`)?.trim())) {
      content.details = { ...editing?.details, level: values.get("detail_level"), certificate_cost: values.get("detail_certificate_cost"),
        languages: values.get("detail_languages").split(",").map((item) => item.trim()).filter(Boolean),
        syllabus: values.get("detail_syllabus").split("\n").map((item) => item.trim()).filter(Boolean),
        ...Object.fromEntries(detailKeys.map((key) => [key, values.get(`detail_${key}`)?.trim() || ""])) };
    }
    if (values.get("enrollment_notes")?.trim() || values.get("enrollment_region")?.trim() || editing?.details?.enrollment) {
      content.details ||= {};
      content.details.enrollment = { status: values.get("enrollment_status"), modality: values.get("enrollment_modality"),
        region: values.get("enrollment_region")?.trim() || "", notes: values.get("enrollment_notes")?.trim() || "",
        minimum_age: values.get("enrollment_age") ? Number(values.get("enrollment_age")) : null,
        checked_on: values.get("enrollment_checked") || null, opens_on: values.get("enrollment_opens") || null,
        closes_on: values.get("enrollment_closes") || null };
    }
    if (!await confirm({ title: "Guardar este recurso", description: "La información se actualizará en el catálogo que consultan los candidatos.", confirmLabel: "Guardar recurso" })) return;
    act(async () => {
      const { data } = editing ? await api.put(`/admin/learning/resources/${editing.id}`, { ...content, version: editing.version }) : await api.post("/admin/learning/resources", content);
      form.reset(); return data;
    });
  }
  return <div className="space-y-5"><PageHeader kicker="Administración" title="Catálogo educativo" description="Gestiona recursos, revisa borradores y controla qué formación se publica para los candidatos." />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{message && <p role="status" className="surface-card p-4">{message}</p>}
    <nav className="workspace-tabs" aria-label="Secciones del catálogo"><button className={view === "library" ? "active" : ""} aria-pressed={view === "library"} onClick={() => setView("library")}>Biblioteca <span>{listedRows.length}</span></button><button className={view === "sources" ? "active" : ""} aria-pressed={view === "sources"} onClick={() => setView("sources")}>Fuentes y conectores</button></nav>
    {view === "sources" && <LearningConnectors onImported={setRows} />}
    {view === "library" && <>
    <div className="surface-card flex flex-wrap items-center justify-between gap-4 p-5"><div><h2 className="text-lg font-bold">Gestión de la biblioteca</h2><p className="mt-1 text-sm text-[var(--muted)]">{rows.filter((row) => !row.url).length} prácticas de TalentSync · {listedRows.filter((row) => row.url).length} recursos externos</p></div><button className="button-primary" onClick={() => { setEditing(null); setStep(0); setFormOpen(!formOpen); }}>{formOpen ? "Cerrar formulario" : "Añadir formación +"}</button></div>
    {(formOpen || editing) && <form id="catalog-editor" key={editing?.id || "new"} onSubmit={save} className="surface-card grid gap-4 p-5 sm:grid-cols-2">
      <div className="sm:col-span-2"><p className="section-kicker">Paso {step + 1} de 3</p><h2 className="mt-2 text-xl font-bold">{["Identifica la formación", "Conecta con las habilidades", "Revisa antes de publicar"][step]}</h2><progress className="mt-4 w-full" value={step + 1} max={3} aria-label="Progreso del recurso" /></div>
      <fieldset data-step="0" hidden={step !== 0} className="catalog-fields sm:col-span-2"><legend className="sr-only">Identificación del recurso</legend>
      {[ ["title", "Nombre del curso o taller", 160], ["provider", "Quién lo ofrece", 120], ["url", "Enlace público del recurso (HTTPS)", 1000] ].map(([name, label, max]) => <label key={name}>{label}<input className="field-control mt-1" name={name} placeholder={({ title: "Ej. Excel para conciliación bancaria", provider: "Ej. Academia que imparte el curso", url: "https://academia.com/curso" })[name]} required maxLength={max} type={name === "url" ? "url" : "text"} defaultValue={name === "skills" ? editing?.skills.join(", ") : editing?.[name] || ""} /></label>)}
      <label>Área<select className="field-control mt-1" name="category" defaultValue={editing?.category || "general"}>{[["general", "Transversales"], ["technology", "Tecnología y datos"], ["service", "Servicio al cliente"], ["sales", "Ventas"], ["administration", "Administración"], ["finance", "Finanzas"], ["logistics", "Logística"], ["education", "Educación"], ["design", "Diseño"], ["care", "Atención en salud"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <p className="text-xs text-[var(--muted)] sm:col-span-2">Usa la página de la formación; el candidato visitará ese enlace para consultar las condiciones.</p></fieldset>
      <fieldset data-step="1" hidden={step !== 1} className="catalog-fields sm:col-span-2"><legend className="sr-only">Contenido y utilidad</legend><label className="sm:col-span-2">Habilidades que podrá reforzar<input className="field-control mt-1" name="skills" required maxLength={2000} placeholder="Ej. excel, conciliación bancaria" defaultValue={editing?.skills.join(", ") || ""} /><span className="text-xs text-[var(--muted)]">Separa por comas. Usa habilidades concretas, como SQL o servicio al cliente.</span></label>
      <label>Tipo<select className="field-control mt-1" name="kind" defaultValue={editing?.kind || "course"}><option value="course">Curso</option><option value="workshop">Taller</option><option value="documentation">Documentación</option></select></label>
      <label>Horas estimadas<input className="field-control mt-1" name="hours" type="number" step="any" min="0.01" max="1000" required defaultValue={editing?.hours || 1} /></label>
      <label>Coste<select className="field-control mt-1" name="cost" defaultValue={editing?.cost || "unknown"}><option value="unknown">Por confirmar</option><option value="free">Gratuito</option><option value="paid">De pago</option></select></label>
      <label className="sm:col-span-2">Qué se aprende y qué practicar<textarea className="field-control mt-1" name="instructions" required minLength={10} maxLength={2000} placeholder="Ej. Aprende a cruzar movimientos, detectar diferencias y preparar una conciliación con una hoja de cálculo." defaultValue={editing?.instructions || ""} /></label>
      <details className="surface-card p-4 sm:col-span-2"><summary className="cursor-pointer font-semibold">Detalle del curso, acceso y certificación</summary><div className="mt-4 grid gap-4 sm:grid-cols-2"><label>Nivel<select className="field-control mt-1" name="detail_level" defaultValue={editing?.details?.level || "any"}>{Object.entries(learningLevels).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label><label>Coste del certificado<select className="field-control mt-1" name="detail_certificate_cost" defaultValue={editing?.details?.certificate_cost || "unknown"}>{Object.entries(certificateCosts).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label><label className="sm:col-span-2">Idiomas del contenido, separados por comas<input className="field-control mt-1" name="detail_languages" maxLength={245} placeholder="es, en" defaultValue={editing?.details?.languages?.join(", ") || ""} /><span className="text-xs text-[var(--muted)]">Hasta seis códigos de idioma confirmados en la fuente.</span></label><label className="sm:col-span-2">Temario del proveedor, un tema por línea<textarea className="field-control mt-1" name="detail_syllabus" rows={4} maxLength={2171} defaultValue={editing?.details?.syllabus?.join("\n") || ""} /><span className="text-xs text-[var(--muted)]">Hasta doce temas de 180 caracteres cada uno.</span></label>{[["prerequisites", "Requisitos previos", 500], ["access_notes", "Condiciones de acceso al curso", 800], ["certificate_notes", "Condiciones del certificado", 800], ["portfolio_idea", "Idea de evidencia propuesta por TalentSync", 600], ["duration_notes", "Referencia de la duración", 400]].map(([key, label, max]) => <label key={key} className="sm:col-span-2">{label}<textarea className="field-control mt-1" name={`detail_${key}`} maxLength={max} defaultValue={editing?.details?.[key] || ""} /></label>)}</div></details>
      <details className="surface-card p-4 sm:col-span-2"><summary className="cursor-pointer font-semibold">Inscripción, modalidad y elegibilidad</summary><div className="mt-4 grid gap-4 sm:grid-cols-2"><label>Disponibilidad<select className="field-control mt-1" name="enrollment_status" defaultValue={editing?.details?.enrollment?.status || "unknown"}>{Object.entries(enrollmentStatuses).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label><label>Modalidad<select className="field-control mt-1" name="enrollment_modality" defaultValue={editing?.details?.enrollment?.modality || "unknown"}>{Object.entries(courseModalities).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label><label>Cobertura o requisitos territoriales<input className="field-control mt-1" name="enrollment_region" maxLength={180} defaultValue={editing?.details?.enrollment?.region || ""} /></label><label>Edad mínima, si aplica<input className="field-control mt-1" name="enrollment_age" type="number" min={0} max={100} defaultValue={editing?.details?.enrollment?.minimum_age ?? ""} /></label>{[["checked", "Fecha de comprobación"], ["opens", "Apertura, si se publica"], ["closes", "Cierre, si se publica"]].map(([key, label]) => <label key={key}>{label}<input type="date" className="field-control mt-1" name={`enrollment_${key}`} defaultValue={editing?.details?.enrollment?.[`${key === "opens" ? "opens" : key === "closes" ? "closes" : "checked"}_on`] || ""} /></label>)}<label className="sm:col-span-2">Condiciones de inscripción<textarea className="field-control mt-1" name="enrollment_notes" maxLength={800} defaultValue={editing?.details?.enrollment?.notes || ""} /></label><p className="text-xs text-[var(--muted)] sm:col-span-2">Una inscripción anunciada necesita fecha de comprobación. Tras 14 días sin comprobar, se mostrará por confirmar. Guardar un plan no reserva un cupo.</p></div></details>
      </fieldset><fieldset data-step="2" hidden={step !== 2} className="catalog-fields sm:col-span-2"><legend className="sr-only">Revisión y publicación</legend><div className="catalog-preview sm:col-span-2"><p className="section-kicker">Vista para el candidato</p><h3 className="mt-2 text-lg font-bold">{preview.title || editing?.title}</h3><p className="mt-1 text-sm text-[var(--muted)]">{preview.provider} · {preview.hours} h · {preview.cost === "free" ? "Gratuito" : preview.cost === "paid" ? "De pago" : "Coste por confirmar"}</p><p className="mt-3 text-sm">{preview.instructions}</p><p className="mt-3 text-xs text-[var(--accent)]">Habilidades: {preview.skills}</p><p className="mt-2 break-all text-xs text-[var(--muted)]">{preview.url}</p></div>
      {[ ["active", "Disponible para planes nuevos"], ["sponsored", "Recurso patrocinado"], ["affiliate", "Enlace con afiliación"] ].map(([name, label]) => <label className="flex items-center gap-2" key={name}><input type="checkbox" name={name} defaultChecked={editing ? editing[name] : name === "active"} />{label}</label>)}
      <label className="sm:col-span-2">Explicación del patrocinio o afiliación<textarea className="field-control mt-1" name="disclosure" maxLength={500} defaultValue={editing?.disclosure || ""} /></label>
      </fieldset><div className="flex flex-wrap gap-3 sm:col-span-2">{step > 0 && <button className="button-secondary" type="button" onClick={() => setStep(step - 1)}><ArrowLeft size={16} />Anterior</button>}{step < 2 ? <button className="button-primary" type="button" onClick={advance}>Continuar<ArrowRight size={16} /></button> : <button className="button-primary" disabled={busy}>Publicar recurso</button>}<button className="button-secondary" type="button" disabled={busy} onClick={() => { setEditing(null); setFormOpen(false); }}>Cancelar</button></div>
    </form>}

    <AdminLearningLibrary rows={listedRows} busy={busy} onEdit={(row) => { setEditing(row); setStep(0); setFormOpen(true); }} />
    <CourseBatchImport onImported={setRows} />
  </>} </div>;
}
