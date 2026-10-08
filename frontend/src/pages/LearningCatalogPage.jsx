import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { LearningResourceCard } from "../components/LearningResourceCard.jsx";

export function LearningCatalogPage() {
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.get("/admin/learning/resources").then(({ data }) => setRows(data)).catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function act(action) {
    setBusy(true); setError(""); setMessage("");
    try { setRows(await action()); setMessage("Catálogo guardado"); setEditing(null); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  function save(event) {
    event.preventDefault(); const form = event.currentTarget; const values = new FormData(form);
    const content = { title: values.get("title"), provider: values.get("provider"), url: values.get("url"), instructions: values.get("instructions"),
      category: values.get("category"), kind: values.get("kind"), hours: Number(values.get("hours")), skills: values.get("skills").split(",").map((item) => item.trim()).filter(Boolean),
      cost: values.get("cost"), sponsored: values.has("sponsored"), affiliate: values.has("affiliate"), disclosure: values.get("disclosure"), active: values.has("active") };
    act(async () => {
      const { data } = editing ? await api.put(`/admin/learning/resources/${editing.id}`, { ...content, version: editing.version }) : await api.post("/admin/learning/resources", content);
      form.reset(); return data;
    });
  }
  return <div className="space-y-5"><PageHeader kicker="Administración" title="Catálogo educativo" description="Asocia cursos y talleres a habilidades concretas. Las recomendaciones se ordenan por utilidad y tiempo, sin ponderar comisiones ni patrocinios." />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{message && <p role="status" className="surface-card p-4">{message}</p>}
    <form key={editing?.id || "new"} onSubmit={save} className="surface-card grid gap-4 p-5 sm:grid-cols-2">
      <h2 className="font-bold sm:col-span-2">{editing ? "Editar recurso" : "Añadir recurso"}</h2>
      {[ ["title", "Título", 160], ["provider", "Proveedor", 120], ["url", "Enlace HTTPS", 1000], ["skills", "Habilidades separadas por comas", 2000] ].map(([name, label, max]) => <label key={name}>{label}<input className="field-control mt-1" name={name} required maxLength={max} type={name === "url" ? "url" : "text"} defaultValue={name === "skills" ? editing?.skills.join(", ") : editing?.[name] || ""} /></label>)}
      <label>Área<select className="field-control mt-1" name="category" defaultValue={editing?.category || "general"}>{[["general", "Transversales"], ["technology", "Tecnología y datos"], ["service", "Servicio al cliente"], ["sales", "Ventas"], ["administration", "Administración"], ["finance", "Finanzas"], ["logistics", "Logística"], ["education", "Educación"], ["design", "Diseño"], ["care", "Atención en salud"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Tipo<select className="field-control mt-1" name="kind" defaultValue={editing?.kind || "course"}><option value="course">Curso</option><option value="workshop">Taller</option><option value="documentation">Documentación</option></select></label>
      <label>Horas estimadas<input className="field-control mt-1" name="hours" type="number" step="0.25" min="0.25" max="1000" required defaultValue={editing?.hours || 1} /></label>
      <label>Coste<select className="field-control mt-1" name="cost" defaultValue={editing?.cost || "unknown"}><option value="unknown">Por confirmar</option><option value="free">Gratuito</option><option value="paid">De pago</option></select></label>
      <label className="sm:col-span-2">Qué se aprende y qué practicar<textarea className="field-control mt-1" name="instructions" required minLength={10} maxLength={2000} defaultValue={editing?.instructions || ""} /></label>
      {[ ["active", "Disponible para planes nuevos"], ["sponsored", "Recurso patrocinado"], ["affiliate", "Enlace con afiliación"] ].map(([name, label]) => <label className="flex items-center gap-2" key={name}><input type="checkbox" name={name} defaultChecked={editing ? editing[name] : name === "active"} />{label}</label>)}
      <label className="sm:col-span-2">Explicación del patrocinio o afiliación<textarea className="field-control mt-1" name="disclosure" maxLength={500} defaultValue={editing?.disclosure || ""} /></label>
      <div className="flex gap-3 sm:col-span-2"><button className="button-primary" disabled={busy}>Guardar recurso</button>{editing && <button className="button-secondary" type="button" disabled={busy} onClick={() => setEditing(null)}>Cancelar edición</button>}</div>
    </form>
    <details className="surface-card p-5"><summary className="cursor-pointer font-bold">Importar catálogo JSON</summary><p className="my-3 text-sm text-[var(--muted)]">Hasta cincuenta recursos por lote y doscientos en total. Usa una lista de objetos con los campos del formulario. No se consultan APIs ni se importan alumnos, compras o certificados.</p><form className="space-y-3" onSubmit={(event) => { event.preventDefault(); const form = event.currentTarget; const value = new FormData(form).get("catalog"); act(async () => { const resources = JSON.parse(value); const { data } = await api.post("/admin/learning/resources/import", { resources }); form.reset(); return data; }); }}><label className="block">Lista JSON<textarea className="field-control mt-1 min-h-36 font-mono" name="catalog" required maxLength={200000} /></label><button className="button-secondary" disabled={busy}>Importar recursos</button></form></details>
    <section className="space-y-4"><h2 className="font-bold">Recursos disponibles y archivados</h2>{rows.map((row) => <div key={row.id} className="surface-card space-y-3 p-4"><LearningResourceCard resource={row} />{row.version ? <button className="button-secondary" disabled={busy} onClick={() => { setEditing(row); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Editar</button> : <p className="text-xs text-[var(--muted)]">Ejercicio original de TalentSync</p>}</div>)}</section>
  </div>;
}
