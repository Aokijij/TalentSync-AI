import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

export function HiringQualityPage() {
  const request = useRef(0);
  const [params] = useSearchParams();
  const [jobs, setJobs] = useState([]), [selected, setSelected] = useState(""), [quality, setQuality] = useState(null);
  const [draft, setDraft] = useState(null), [search, setSearch] = useState("");
  const [error, setError] = useState(""), [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  useEffect(() => {
    Promise.all([api.get("/organization/me"), api.get("/jobs", { params: { status: "" } })]).then(([a, b]) => {
      const own = b.data.filter((job) => job.company_id === a.data.id); setJobs(own);
      const initial = own.find((job) => String(job.id) === params.get("vacante")) || own[0];
      if (initial) choose(initial);
    }).catch((failure) => setError(getApiErrorMessage(failure)));
  }, []);
  async function choose(job) {
    const revision = ++request.current;
    setSelected(String(job.id)); setQuality(null); setError(""); setMessage("");
    setDraft({ ...job, skill_requirements: job.skill_requirements?.length ? job.skill_requirements : (job.skills || []).map((skill) => ({ skill, essential: false, weight: 1 })) });
    try { const response = await api.get(`/hiring/quality/${job.id}`); if (revision === request.current) setQuality(response.data); } catch (failure) { if (revision === request.current) setError(getApiErrorMessage(failure)); }
  }
  function update(key, value) { setDraft((current) => ({ ...current, [key]: value })); }
  function skill(index, key, value) { update("skill_requirements", draft.skill_requirements.map((row, i) => i === index ? { ...row, [key]: value } : row)); }
  async function save(event) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const { data } = await api.patch(`/jobs/${selected}`, { title: draft.title, description: draft.description, requirements: draft.requirements, salary: draft.salary == null || draft.salary === "" ? null : Number(draft.salary), location: draft.location || null, modality: draft.modality, response_days: Number(draft.response_days), skill_requirements: draft.skill_requirements });
      setJobs(jobs.map((job) => job.id === data.id ? data : job)); setDraft(data); setQuality((await api.get(`/hiring/quality/${selected}`)).data); setMessage("Oferta actualizada y revisión recalculada. Los requisitos se usarán en la compatibilidad.");
    } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <div className="space-y-5"><PageHeader kicker="Centro de contratación" title="Mejora la calidad de tus ofertas" description="Detecta información incompleta, aclara los requisitos y corrige la oferta desde una sola revisión." />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{message && <p role="status" className="surface-card p-4">{message}</p>}
    <section className="surface-card grid gap-3 p-5 sm:grid-cols-2"><label>Buscar una vacante<input className="field-control mt-1" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nombre del cargo" /></label><label>Vacante<select className="field-control mt-1" value={selected} disabled={busy} onChange={(event) => { const job = jobs.find((row) => String(row.id) === event.target.value); if (job) choose(job); }}><option value="">Selecciona una vacante</option>{jobs.filter((job) => String(job.id) === selected || job.title.toLowerCase().includes(search.toLowerCase())).map((job) => <option key={job.id} value={job.id}>{job.title} · {job.status === "draft" ? "Borrador" : job.status === "active" ? "Activa" : "Cerrada"}</option>)}</select></label>{!jobs.length && <Link className="text-[var(--accent)]" to="/empresa/vacantes">Crear mi primera vacante</Link>}</section>
    {quality && draft && <div className="grid items-start gap-5 lg:grid-cols-[300px_1fr]">
      <section className="surface-card space-y-4 p-5"><h2 className="font-bold">Claridad de la oferta · {quality.completeness}%</h2><progress aria-label="Claridad de oferta" value={quality.completeness} max={100} className="w-full" /><p className="text-xs text-[var(--muted)]">Lista de revisión orientativa; no garantiza calidad ni cumplimiento normativo.</p>{quality.checks.map((check) => <div className="border-t border-[var(--line)] pt-3" key={check.key}><p className="text-sm font-semibold">{check.passed ? "✓" : "Pendiente"} · {check.label}</p>{!check.passed && <><p className="mt-1 text-xs text-[var(--muted)]">{check.action}</p><a className="text-xs text-[var(--accent)]" href={`#quality-${check.key === "inclusive" ? "requirements" : check.key}`}>Revisar campo</a></>}</div>)}{quality.issues.map((issue) => <p key={issue.code} className="rounded-lg bg-[var(--surface-subtle)] p-3 text-sm">{issue.message}</p>)}<details><summary className="cursor-pointer text-sm font-semibold">Referencia salarial local</summary><p className="mt-2 text-sm">{quality.salary_reference.median ? `$${quality.salary_reference.median.toLocaleString("es-CO")} COP · ${quality.salary_reference.sample_size} ofertas comparables` : "Se necesitan al menos cinco ofertas comparables."}</p><p className="mt-2 text-xs text-[var(--muted)]">{quality.salary_reference.notice}</p></details><p className="text-xs">{quality.blind_hiring ? "Selección ciega activa" : "Identidad visible en este proceso"}</p></section>
      <form className="surface-card space-y-4 p-5" onSubmit={save}><h2 className="font-bold">Editar y volver a revisar</h2>
        <label className="block" id="quality-title">Cargo<input className="field-control mt-1" required minLength={2} maxLength={180} value={draft.title} onChange={(event) => update("title", event.target.value)} /></label>
        <label className="block" id="quality-description">Responsabilidades y contexto<textarea className="field-control mt-1 min-h-28" required minLength={10} value={draft.description} onChange={(event) => update("description", event.target.value)} /></label>
        <label className="block" id="quality-requirements">Experiencia y requisitos<textarea className="field-control mt-1 min-h-24" required minLength={10} value={draft.requirements} onChange={(event) => update("requirements", event.target.value)} /></label>
        <div className="grid gap-3 sm:grid-cols-2"><label id="quality-salary">Salario mensual (COP)<input className="field-control mt-1" type="number" min={1} value={draft.salary ?? ""} onChange={(event) => update("salary", event.target.value)} /></label><label id="quality-response_days">Respuesta por avance (días)<input className="field-control mt-1" required type="number" min={1} max={30} value={draft.response_days || 7} onChange={(event) => update("response_days", event.target.value)} /></label><label id="quality-location">Ciudad<input className="field-control mt-1" value={draft.location || ""} onChange={(event) => update("location", event.target.value)} /></label><label>Modalidad<select className="field-control mt-1" value={draft.modality} onChange={(event) => update("modality", event.target.value)}><option value="remote">Remota</option><option value="hybrid">Híbrida</option><option value="onsite">Presencial</option></select></label></div>
        <fieldset className="space-y-3" id="quality-skill_requirements"><legend className="mb-2 font-bold">Habilidades que se comparan con los perfiles</legend><p className="text-xs text-[var(--muted)]">Marca esenciales y asigna peso de 1 a 5. Una habilidad relacionada indica una base para aprender; no equivale a cumplir el requisito.</p>{draft.skill_requirements.map((row, index) => <div key={index} className="grid items-end gap-2 rounded-xl border border-[var(--line)] p-3 sm:grid-cols-[1fr_auto_85px_auto]"><label>Habilidad<input className="field-control mt-1" required maxLength={100} value={row.skill} onChange={(event) => skill(index, "skill", event.target.value)} /></label><label className="flex items-center gap-2 pb-3"><input type="checkbox" checked={row.essential} onChange={(event) => skill(index, "essential", event.target.checked)} />Esencial</label><label>Peso<input className="field-control mt-1" type="number" required min={1} max={5} value={row.weight} onChange={(event) => skill(index, "weight", Number(event.target.value))} /></label><button type="button" className="button-secondary" onClick={() => update("skill_requirements", draft.skill_requirements.filter((_, i) => i !== index))}>Quitar</button></div>)}<button type="button" className="button-secondary" disabled={draft.skill_requirements.length >= 50} onClick={() => update("skill_requirements", [...draft.skill_requirements, { skill: "", essential: false, weight: 1 }])}>Añadir habilidad</button></fieldset>
        <div className="flex flex-wrap gap-3"><button className="button-primary" disabled={busy}>Guardar y recalcular revisión</button><Link className="button-secondary" to="/empresa/vacantes">Gestionar publicación</Link></div>
      </form>
    </div>}
  </div>;
}
