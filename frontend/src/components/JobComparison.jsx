import { useState } from "react";
import { ArrowRight, Check, Columns3, Minus, X } from "lucide-react";
import { Link } from "react-router-dom";
import { CoachDialog } from "./CoachDialog.jsx";
import { comparisonFacts, comparisonRequirements, COMPARISON_LIMIT } from "../utils/jobComparison.js";
import { skillName } from "../utils/skillNames.js";
import "../styles/job-comparison.css";

export function JobComparison({ selection, jobs, matches, loading, returnTo, applications = {} }) {
  const [open, setOpen] = useState(false);
  const byId = new Map(jobs.map((job) => [job.id, job]));
  const selected = selection.ids.map((id) => byId.get(id)).filter(Boolean);
  if (!selection.ids.length) return null;
  return <>
    <section className="comparison-tray" aria-label="Vacantes para comparar">
      <div className="comparison-tray-title"><Columns3 size={21} /><div><strong><span className="comparison-heading-label">Tu comparación</span><span className="comparison-count" aria-live="polite">{selection.ids.length}/{COMPARISON_LIMIT}</span></strong><p>{selected.length < 2 ? "Elige otra vacante para comparar sus condiciones." : "Revisa tus opciones y elige tu próximo paso."}</p></div></div>
      <ul className="comparison-selection" aria-label="Vacantes seleccionadas">{selection.ids.map((id) => <li key={id}><span title={byId.get(id)?.title}>{byId.get(id)?.title || (loading ? "Cargando oferta…" : "Oferta no disponible")}</span><button type="button" aria-label={`Quitar ${byId.get(id)?.title || "oferta no disponible"} de la comparación`} onClick={() => selection.toggle(id)}><X size={14} /></button></li>)}</ul>
      <div className="comparison-tray-actions">{!!selection.ids.length && <button type="button" aria-label="Limpiar comparación" className="button-secondary button-sm comparison-clear" onClick={selection.clear}><X size={16} /><span>Limpiar</span></button>}<button type="button" className="button-primary button-sm" disabled={selected.length < 2 || loading} onClick={() => setOpen(true)}><Columns3 size={16} />Comparar{selected.length > 0 ? ` (${selected.length})` : ""}</button></div>
    </section>
    <CoachDialog open={open} onClose={() => setOpen(false)} title="Compara las vacantes" Icon={Columns3} className="job-comparison-dialog">
      <JobComparisonTable jobs={selected} matches={matches} returnTo={returnTo} applications={applications} />
    </CoachDialog>
  </>;
}

const fields = [["salary", "Salario publicado"], ["modality", "Modalidad"], ["location", "Ubicación o alcance remoto"], ["contract", "Contrato"], ["schedule", "Jornada y horario"], ["experience", "Experiencia mínima"], ["education", "Formación solicitada"], ["languages", "Idiomas"], ["benefits", "Beneficios"], ["process", "Plazos del proceso"]];

export function JobComparisonTable({ jobs, matches = {}, returnTo, applications = {} }) {
  const [differentOnly, setDifferentOnly] = useState(false);
  const facts = jobs.map(comparisonFacts);
  return <div className="comparison-workspace">
    <div className="comparison-intro"><p>Compara condiciones publicadas y el ajuste de tu perfil. La compatibilidad no representa una probabilidad de contratación.</p><label><input type="checkbox" checked={differentOnly} onChange={(event) => setDifferentOnly(event.target.checked)} />Mostrar solo condiciones diferentes</label></div>
    <p className="comparison-scroll-hint">En pantallas pequeñas, desliza la tabla para comparar las ofertas.</p>
    <div className="comparison-scroll" role="region" aria-label="Tabla de comparación de vacantes" tabIndex={0}>
      <table className="comparison-table"><caption className="sr-only">Condiciones y requisitos de {jobs.length} vacantes seleccionadas</caption><thead><tr><th scope="col">Qué ofrece cada vacante</th>{jobs.map((job) => <th scope="col" key={job.id}><span>{job.company_name || "Empresa"}</span><h3>{job.title}</h3>{applications[job.id] && <span className="comparison-applied"><Check size={14} />Postulación enviada</span>}<small>{job.source_kind === "external" ? "Oferta externa · confirma los datos en el origen" : "Publicada en TalentSync"}</small><Link className="button-secondary button-sm" to={`/vacantes/${job.id}`} state={{ returnTo }}>Ver oferta<ArrowRight size={14} /></Link></th>)}</tr></thead><tbody>
        <tr><th scope="row">Compatibilidad con tu perfil</th>{jobs.map((job) => { const match = matches[job.id]; return <td key={job.id}>{match?.match_percentage != null ? <><strong className="comparison-score">{Math.round(match.match_percentage)}%</strong><small>{match.is_estimated || job.source_kind === "external" ? "Estimación con los datos disponibles" : "Según tu perfil actual"}</small></> : <span className="comparison-unknown">Sin cálculo disponible</span>}</td>; })}</tr>
        {fields.filter(([key]) => !differentOnly || new Set(facts.map((row) => row[key])).size > 1).map(([key, label]) => <tr key={key}><th scope="row">{label}</th>{jobs.map((job, index) => <td key={job.id}>{facts[index][key]}</td>)}</tr>)}
        <tr><th scope="row">Habilidades solicitadas</th>{jobs.map((job) => <td key={job.id}><SkillList skills={(job.skill_requirements?.length ? job.skill_requirements.map((row) => row.skill) : job.skills) || []} empty="Sin habilidades especificadas" /></td>)}</tr>
        <tr><th scope="row">Habilidades cumplidas</th>{jobs.map((job) => { const requirements = comparisonRequirements(matches[job.id]); return <td key={job.id}>{requirements ? <SkillList skills={requirements.covered.map((row) => row.skill)} empty="Ninguna confirmada por el cálculo" met /> : <span className="comparison-unknown">Sin detalle disponible</span>}</td>; })}</tr>
        <tr><th scope="row">Habilidades por reforzar o confirmar</th>{jobs.map((job) => { const requirements = comparisonRequirements(matches[job.id]); return <td key={job.id}>{requirements ? <SkillList skills={requirements.pending.map((row) => row.skill)} empty="Sin habilidades pendientes en el cálculo" /> : <span className="comparison-unknown">Sin detalle disponible</span>}</td>; })}</tr>
      </tbody></table>
    </div>
    <p className="comparison-footnote">Los campos sin especificar requieren confirmación con la empresa. No calculamos un ganador: elige según tus prioridades.</p>
  </div>;
}

function SkillList({ skills, empty, met = false }) {
  if (!skills.length) return <span className="comparison-unknown">{empty}</span>;
  return <ul className="comparison-skills">{[...new Set(skills)].map((skill) => <li key={skill}>{met ? <Check size={13} /> : <Minus size={13} />}{skillName(skill)}</li>)}</ul>;
}
