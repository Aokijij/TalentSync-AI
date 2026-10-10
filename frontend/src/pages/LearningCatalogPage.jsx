import { BookOpen, Link2, Sparkles, CheckCircle2, ArrowRight, ArrowLeft } from "lucide-react";
import { LearningFilters } from "../components/LearningFilters.jsx";
import { filterResources } from "../utils/learningFilters.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { LearningResourceCard } from "../components/LearningResourceCard.jsx";
import { LearnCatalogImport } from "../components/LearnCatalogImport.jsx";

export function LearningCatalogPage() {
  const { confirm } = useFeedback();
  const [step, setStep] = useState(0), [preview, setPreview] = useState({});
  function advance(event) { event.preventDefault(); const form = event.currentTarget.closest("form"); const fields = [...form.querySelectorAll(`fieldset[data-step="${step}"] input, fieldset[data-step="${step}"] textarea, fieldset[data-step="${step}"] select`)]; if (fields.some((field) => !field.reportValidity())) return; setPreview(Object.fromEntries(new FormData(form))); setStep(step + 1); }
  const [filters, setFilters] = useState({}), [formOpen, setFormOpen] = useState(false), [page, setPage] = useState(1);
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (formOpen) document.getElementById("catalog-editor")?.scrollIntoView({ block: "start", behavior: "smooth" }); }, [formOpen, step]);
  useEffect(() => { api.get("/admin/learning/resources").then(({ data }) => setRows(data)).catch((failure) => setError(getApiErrorMessage(failure))); }, []);
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
    if (!await confirm({ title: "Guardar este recurso", description: "La información se actualizará en el catálogo que consultan los candidatos.", confirmLabel: "Guardar recurso" })) return;
    act(async () => {
      const { data } = editing ? await api.put(`/admin/learning/resources/${editing.id}`, { ...content, version: editing.version }) : await api.post("/admin/learning/resources", content);
      form.reset(); return data;
    });
  }
  return <div className="space-y-5"><PageHeader kicker="Administración" title="Catálogo educativo" description="Asocia cursos y talleres a habilidades concretas. Las recomendaciones se ordenan por utilidad y tiempo, sin ponderar comisiones ni patrocinios." />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{message && <p role="status" className="surface-card p-4">{message}</p>}
    <LearnCatalogImport onImported={setRows} />
    <div className="surface-card flex flex-wrap items-center justify-between gap-4 p-5"><div><h2 className="text-lg font-bold">Biblioteca de aprendizaje</h2><p className="mt-1 text-sm text-[var(--muted)]">{rows.filter((row) => !row.url).length} prácticas de TalentSync · {rows.filter((row) => row.url).length} recursos externos</p></div><button className="button-primary" onClick={() => { setEditing(null); setStep(0); setFormOpen(!formOpen); }}>{formOpen ? "Cerrar formulario" : "Añadir formación +"}</button></div>
    <section className="catalog-guide"><div><span className="learning-area-icon"><BookOpen size={23} /></span><h2 className="mt-3 text-lg font-bold">¿Qué puedes añadir?</h2><p className="mt-2 text-sm leading-6 text-[var(--muted)]">Un curso, taller o guía con enlace público. TalentSync lo recomendará cuando sus habilidades ayuden a cerrar una brecha. Las prácticas internas ya vienen en la biblioteca.</p></div><ol>{[[Link2, "1. Identifica el recurso", "Título, proveedor y enlace a su página."], [Sparkles, "2. Describe su utilidad", "Habilidades que enseña, área, tiempo y coste."], [CheckCircle2, "3. Revisa y publica", "Comprueba lo que verá el candidato."]].map(([Icon, title, copy]) => <li key={title}><Icon size={20} /><div><strong>{title}</strong><p>{copy}</p></div></li>)}</ol></section>
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
      </fieldset><fieldset data-step="2" hidden={step !== 2} className="catalog-fields sm:col-span-2"><legend className="sr-only">Revisión y publicación</legend><div className="catalog-preview sm:col-span-2"><p className="section-kicker">Vista para el candidato</p><h3 className="mt-2 text-lg font-bold">{preview.title || editing?.title}</h3><p className="mt-1 text-sm text-[var(--muted)]">{preview.provider} · {preview.hours} h · {preview.cost === "free" ? "Gratuito" : preview.cost === "paid" ? "De pago" : "Coste por confirmar"}</p><p className="mt-3 text-sm">{preview.instructions}</p><p className="mt-3 text-xs text-[var(--accent)]">Habilidades: {preview.skills}</p><p className="mt-2 break-all text-xs text-[var(--muted)]">{preview.url}</p></div>
      {[ ["active", "Disponible para planes nuevos"], ["sponsored", "Recurso patrocinado"], ["affiliate", "Enlace con afiliación"] ].map(([name, label]) => <label className="flex items-center gap-2" key={name}><input type="checkbox" name={name} defaultChecked={editing ? editing[name] : name === "active"} />{label}</label>)}
      <label className="sm:col-span-2">Explicación del patrocinio o afiliación<textarea className="field-control mt-1" name="disclosure" maxLength={500} defaultValue={editing?.disclosure || ""} /></label>
      </fieldset><div className="flex flex-wrap gap-3 sm:col-span-2">{step > 0 && <button className="button-secondary" type="button" onClick={() => setStep(step - 1)}><ArrowLeft size={16} />Anterior</button>}{step < 2 ? <button className="button-primary" type="button" onClick={advance}>Continuar<ArrowRight size={16} /></button> : <button className="button-primary" disabled={busy}>Publicar recurso</button>}<button className="button-secondary" type="button" disabled={busy} onClick={() => { setEditing(null); setFormOpen(false); }}>Cancelar</button></div>
    </form>}

    <LearningFilters value={filters} onChange={(value) => { setFilters(value); setPage(1); }} /><section className="space-y-4"><h2 className="font-bold">Recursos disponibles y archivados · {filterResources(rows, filters).length}</h2><div className="grid gap-4 lg:grid-cols-2">{filterResources(rows, filters).slice((page - 1) * 10, page * 10).map((row) => <div key={row.id} className="surface-card space-y-3 p-4"><LearningResourceCard resource={row} />{row.version ? <button className="button-secondary" disabled={busy} onClick={() => { setEditing(row); setStep(0); setFormOpen(true); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Editar</button> : <p className="text-xs text-[var(--muted)]">{row.url ? "Referencia externa incluida en la biblioteca" : "Ejercicio original de TalentSync"}</p>}</div>)}</div><div className="flex flex-wrap items-center gap-3"><button className="button-secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button><span className="text-sm">Página {page} de {Math.max(1, Math.ceil(filterResources(rows, filters).length / 10))}</span><button className="button-secondary" disabled={page * 10 >= filterResources(rows, filters).length} onClick={() => setPage(page + 1)}>Siguiente</button></div></section>
    <details className="surface-card p-5"><summary className="cursor-pointer font-bold">Opciones avanzadas · importar un lote JSON</summary><p className="my-3 text-sm text-[var(--muted)]">Hasta cincuenta recursos por lote y doscientos en total. Usa una lista de objetos con los campos del formulario. No se consultan APIs ni se importan alumnos, compras o certificados.</p><form className="space-y-3" onSubmit={async (event) => { event.preventDefault(); const form = event.currentTarget; const value = new FormData(form).get("catalog"); if (!await confirm({ title: "Importar estos recursos", description: "El lote se añadirá al catálogo educativo que consultan los candidatos.", confirmLabel: "Importar recursos" })) return; act(async () => { const resources = JSON.parse(value); const { data } = await api.post("/admin/learning/resources/import", { resources }); form.reset(); return data; }); }}><label className="block">Lista JSON<textarea className="field-control mt-1 min-h-36 font-mono" name="catalog" required maxLength={200000} /></label><button className="button-secondary" disabled={busy}>Importar recursos</button></form></details>
  </div>;
}
