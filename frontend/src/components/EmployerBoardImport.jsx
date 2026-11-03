import { useState } from "react";
import { CheckCircle2, ExternalLink, Search, ShieldCheck, RefreshCw, Download } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import "../styles/external-vacancies.css";

export function EmployerBoardImport({ onChanged }) {
  const [board, setBoard] = useState(""), [query, setQuery] = useState(""), [location, setLocation] = useState("Colombia");
  const [preview, setPreview] = useState(null), [selected, setSelected] = useState([]), [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(""), [error, setError] = useState(""), [result, setResult] = useState("");
  const reset = (setter) => (event) => { setter(event.target.value); setPreview(null); setSelected([]); setResult(""); };
  async function search(event) {
    event.preventDefault(); setBusy("preview"); setError(""); setResult("");
    try { const { data } = await api.post("/admin/jobs/sources/ats/preview", { board_url: board, keywords: query, location }, { __quiet: true }); setPreview(data); setSelected([]); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(""); }
  }
  async function importSelected() {
    setBusy("import"); setError("");
    try { const { data } = await api.post("/admin/jobs/sources/ats/import", { board_url: board, keywords: query, location, selected_ids: selected, authorized }, { __quiet: true }); setResult(`${data.created} creadas · ${data.updated} actualizadas · ${data.rejected} rechazadas. Solo las ofertas confirmadas en la fuente aparecerán al candidato.`); setPreview(null); setSelected([]); onChanged?.(); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(""); }
  }
  async function checkPending() {
    setBusy("check"); setError("");
    try { const { data } = await api.post("/admin/jobs/availability/check", {}, { __quiet: true }); setResult(`${data.checked} comprobadas: ${data.verified} vigentes, ${data.closed} cerradas, ${data.unknown + data.unavailable} sin confirmar.`); onChanged?.(); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(""); }
  }
  return <section className="external-board-workspace">
    <header><span className="external-board-icon"><ShieldCheck size={22} /></span><div><p className="section-kicker">FUENTES ORIGINALES</p><h3>Vacantes externas, con vigencia comprobada</h3><p>Consulta el portal de una empresa en Greenhouse o Lever. Revisa y selecciona las ofertas antes de incorporarlas.</p></div><span className="external-board-tag">Consulta directa</span></header>
    <form onSubmit={search} className="external-board-form"><label>Portal de empleos de la empresa<input type="url" className="field-control" required value={board} onChange={reset(setBoard)} placeholder="Pega la dirección del portal de Greenhouse o Lever" /><small>Usa el portal completo de la empresa, sin abrir una vacante concreta.</small></label><label>Cargo o habilidad<input className="field-control" value={query} onChange={reset(setQuery)} placeholder="Opcional · limita por contenido" /></label><label>Ubicación publicada<input className="field-control" value={location} onChange={reset(setLocation)} placeholder="Vacío para cualquier ubicación" /></label><button className="button-primary" disabled={!!busy}><Search size={16} />{busy === "preview" ? "Consultando…" : "Consultar portal"}</button></form>
    {error && <p role="alert" className="external-board-message is-error">{error}</p>}{result && <p role="status" className="external-board-message"><CheckCircle2 size={17} />{result}</p>}
    {preview && <div className="external-board-preview"><div><strong>{preview.provider} · {preview.items.length} coincidencias</strong><p>{preview.note}</p></div>{preview.items.length ? <><ul>{preview.items.map((job) => <li key={job.id}><label><input type="checkbox" checked={selected.includes(job.id)} disabled={!!busy || job.eligible === false || !selected.includes(job.id) && selected.length >= 50} onChange={(event) => setSelected((previous) => event.target.checked ? [...previous, job.id] : previous.filter((id) => id !== job.id))} /><span><strong>{job.title}</strong><small>{job.company} · {job.location || "Ubicación sin especificar"}</small><small>{job.skills?.length ?? 0} habilidades identificadas{job.published_at ? ` · ${new Date(job.published_at).toLocaleDateString("es-CO", { timeZone: "UTC" })}` : " · Fecha sin confirmar"}</small>{job.eligible === false && <small className="text-[var(--warning)]">{job.rejection_reasons?.map((reason) => ({ publication_missing: "Falta la fecha de fuente", publication_too_old: "Más de tres meses", publication_in_future: "Fecha no válida", insufficient_skills: "Menos de tres habilidades", responsibilities_unclear: "Funciones insuficientes", requirements_unclear: "Requisitos insuficientes", experience_unspecified: "Experiencia sin especificar", education_unspecified: "Formación sin especificar" }[reason])).filter(Boolean).join(" · ")}</small>}</span></label><a href={job.url} target="_blank" rel="noopener noreferrer" className="button-secondary button-sm" aria-label={`Revisar fuente de ${job.title}`}><ExternalLink size={14} />Fuente</a></li>)}</ul><label className="external-board-consent"><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} />He revisado la fuente y tengo autorización para incorporar estas publicaciones conservando su origen.</label><button className="button-primary" type="button" disabled={!!busy || !authorized || !selected.length} onClick={importSelected}><Download size={16} />{busy === "import" ? "Incorporando…" : `Incorporar selección (${selected.length})`}</button></> : <p>No hay coincidencias en esta muestra del portal. Revisa la ubicación: «remoto» no confirma que se pueda trabajar desde Colombia.</p>}</div>}
    <footer><div><strong>Comprobaciones automáticas</strong><p>Se vuelve a consultar cada oferta a partir de las 24 horas. Si no se confirma o pasan 72 horas sin una comprobación válida, deja de recomendarse. Un fallo temporal no se presenta como cierre.</p></div><button type="button" className="button-secondary" disabled={!!busy} onClick={checkPending}><RefreshCw size={16} />{busy === "check" ? "Comprobando…" : "Actualizar comprobaciones"}</button></footer>
  </section>;
}
