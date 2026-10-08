import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

export function PersonalizationPage() {
  const [signals, setSignals] = useState([]); const [jobs, setJobs] = useState([]); const [enabled, setEnabled] = useState(false);
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState("");
  async function load() {
    const [a, b, c] = await Promise.all([api.get("/personalization/feedback"), api.get("/jobs"), api.get("/account/privacy")]);
    setSignals(a.data); setJobs(b.data); setEnabled(c.data.personalize_recommendations);
  }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function act(action) { setBusy(true); setError(""); setNotice(""); try { await action(); await load(); setNotice("Preferencia actualizada"); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }
  return <div className="space-y-5"><PageHeader kicker="Recomendaciones a tu medida" title="Mis intereses" description="Indica qué ofertas te interesan. Se utiliza para ordenar oportunidades y ocultar las que descartes; el índice de afinidad técnica se conserva." />
    {error && <p role="alert" className="text-[var(--error)]">{error}</p>}{notice && <p role="status">{notice}</p>}
    <section className="surface-card space-y-3 p-5"><h2 className="font-bold">Personalización {enabled ? "activada" : "desactivada"}</h2><p className="text-sm text-[var(--muted)]">Solo se registran tus decisiones explícitas con tu consentimiento. Desactivarla borra tus interacciones y los modelos experimentales que pudieran incluirlas. No se registra tu navegación.</p><Link className="button-outline inline-flex" to="/seguridad">Configurar consentimiento en Seguridad</Link></section>
    <form className="surface-card grid gap-3 p-5 sm:grid-cols-3" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); act(() => api.put("/personalization/feedback", { job_id: Number(form.get("job")), interested: form.get("interested") === "true" })); }}><label>Vacante<select className="field-control mt-1" name="job" required disabled={!enabled || busy}><option value="">Selecciona una oferta</option>{jobs.map((job) => <option value={job.id} key={job.id}>{job.title} · {job.company_name}</option>)}</select></label><label>Mi interés<select className="field-control mt-1" name="interested" disabled={!enabled || busy}><option value="true">Me interesa</option><option value="false">Ocultar de recomendaciones</option></select></label><button className="button-primary self-end" disabled={!enabled || busy}>Guardar interés</button></form>
    <section className="space-y-3"><h2 className="font-bold">Decisiones guardadas</h2>{!signals.length && <p className="text-[var(--muted)]">Aún no hay decisiones guardadas.</p>}{signals.map((row) => <article className="surface-card flex flex-wrap items-center justify-between gap-3 p-5" key={row.job_id}><div><Link className="font-semibold text-[var(--accent)]" to={`/vacantes/${row.job_id}`}>{row.title}</Link><p className="text-sm">{row.interested ? "Me interesa" : "Oculta de mis recomendaciones"}</p></div><button className="button-outline" disabled={busy} onClick={() => act(() => api.delete(`/personalization/feedback/${row.job_id}`))}>Deshacer decisión</button></article>)}</section>
    <Link className="button-primary inline-flex" to="/recomendaciones">Ver mis recomendaciones</Link>
  </div>;
}

const statuses = { insufficient_data: "Faltan datos reales", insufficient_validation_data: "Faltan datos de validación", validated_shadow: "Validado en evaluación; fuera del ranking", needs_review_shadow: "Requiere revisión; fuera del ranking", invalidated_consent_withdrawal: "Invalidado por retirada de consentimiento", invalidated_feedback_removal: "Invalidado por retirada de una señal" };

export function ModelPage() {
  const [data, setData] = useState(null); const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState("");
  async function load() { setData((await api.get("/admin/models")).data); }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  return <div className="space-y-5"><PageHeader kicker="MLOps local" title="Motor e integraciones" description="Consulta el método activo, la suficiencia de los datos y los resultados de los experimentos. Los modelos experimentales no se activan automáticamente en selección." />
    {error && <p role="alert" className="text-[var(--error)]">{error}</p>}{notice && <p role="status">{notice}</p>}
    {data && <>
      <section className="surface-card space-y-3 p-5"><h2 className="font-bold">Método activo</h2><p className="break-all font-mono text-sm">{data.version}</p><p className="text-sm text-[var(--muted)]">{data.notice}</p><p>{data.observed_processes} procesos observados · {data.processes_advanced_to_interview} avanzados a entrevista. Se excluyen cuentas ficticias.</p><Link className="button-outline inline-flex" to="/admin/ecosistema">Ver auditoría y distribución</Link></section>
      <section className="surface-card space-y-4 p-5"><h2 className="font-bold">Aprendizaje de interés declarado</h2><div className="grid gap-3 sm:grid-cols-4">{[["rows", "Decisiones"], ["users", "Candidatos"], ["jobs", "Vacantes"], ["positives", "Intereses positivos"]].map(([key, label]) => <div key={key} className="rounded-lg bg-[var(--surface-subtle)] p-4"><p className="text-sm">{label}</p><p className="text-2xl font-bold">{data.training_data[key]}</p></div>)}</div><p className="text-sm">Se necesitan al menos {data.minimum_data.rows} decisiones, {data.minimum_data.users} candidatos, {data.minimum_data.jobs} vacantes y {data.minimum_data.each_label} casos de cada respuesta. Se separan usuarios entre entrenamiento y evaluación.</p><p className="text-sm">{data.training_data.ready ? "Hay datos suficientes para ejecutar la evaluación." : "Muestra insuficiente. Los datos de demostración no entrenan el modelo."}</p><button className="button-primary" disabled={busy} onClick={async () => { setBusy(true); setError(""); try { const { data: result } = await api.post("/admin/models/train"); setNotice(statuses[result.status] || result.status); await load(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }}>Evaluar entrenamiento local</button></section>
      <section className="surface-card space-y-3 p-5"><h2 className="font-bold">Historial de experimentos</h2>{!data.experiments.length && <p className="text-sm text-[var(--muted)]">Aún no se han registrado experimentos.</p>}{data.experiments.map((row) => <article className="border-t border-[var(--line)] pt-3" key={row.id}><h3 className="font-semibold">#{row.id} · {statuses[row.status] || row.status}</h3><p className="break-all text-xs text-[var(--muted)]">{row.version}</p>{row.metrics.auc != null && <p className="mt-2 text-sm">AUC: {row.metrics.auc} · Brier: {row.metrics.brier} · referencia: {row.metrics.baseline_brier} · {row.metrics.test_rows} muestras de validación.</p>}</article>)}</section>
      <section className="surface-card space-y-3 p-5"><h2 className="font-bold">Estado de integraciones</h2>{data.integrations.map((row) => <div className="border-t border-[var(--line)] pt-3" key={row.name}><h3 className="font-semibold">{row.name}</h3><p className="text-sm text-[var(--muted)]">{row.status}</p></div>)}</section>
    </>}
  </div>;
}
