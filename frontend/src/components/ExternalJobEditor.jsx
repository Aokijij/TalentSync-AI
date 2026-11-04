import { useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";
import { externalJobFields, externalJobChanges } from "../utils/externalJobEditor.js";
import { CurrencyInput } from "./CurrencyInput.jsx";
import { LanguagesEditor } from "./LanguagesEditor.jsx";
import { WorkScheduleEditor } from "./WorkScheduleEditor.jsx";
import { RemoteScopeEditor } from "./RemoteScopeEditor.jsx";
import { CredentialRequirementsEditor } from "./CredentialRequirementsEditor.jsx";
import { EDUCATION_LEVELS } from "../constants/educationLevels.js";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import "../styles/external-job-editor.css";

const split = text => [...new Set(text.split(",").map(item => item.trim()).filter(Boolean))];
const number = value => value === "" ? null : Number(value);
const levels = { unspecified: "Sin nivel indicado", basic: "Básico", intermediate: "Intermedio", advanced: "Avanzado", expert: "Experto" };
export function ExternalJobEditor({ data, busy, setBusy, onError, onSaved }) {
  const [baseline] = useState(() => externalJobFields(data));
  const [values, setValues] = useState(() => structuredClone(baseline));
  const [skillText, setSkillText] = useState(() => baseline.skill_requirements.map(row => row.skill).join(", "));
  const [studyText, setStudyText] = useState(() => baseline.required_study_fields.join(", "));
  const [section, setSection] = useState("content"), [note, setNote] = useState("");
  const change = (key, value) => setValues(current => ({ ...current, [key]: value }));
  const quality = (key, value) => setValues(current => ({ ...current, quality_details: { ...current.quality_details, [key]: value } }));
  const q = values.quality_details, changed = externalJobChanges(baseline, values);
  const skill = (index, key, value) => change("skill_requirements", values.skill_requirements.map((row, i) => i === index ? { ...row, [key]: value } : row));
  async function submit(event) {
    event.preventDefault(); setBusy(true); onError("");
    try {
      const { data: updated } = await api.patch(`/admin/jobs/${data.id}/content`, { revision: data.moderation_revision, source_url: data.external_url, note: note.trim(), fields: changed }, { __skipRetry: true });
      await onSaved(updated);
    } catch (error) { onError(getApiErrorMessage(error)); } finally { setBusy(false); }
  }
  return <form className="external-job-editor" onSubmit={submit}>
    <p>Completa los datos que figuran en la oferta original. Puedes guardar cada apartado y volver a editarlo, aunque falte información en los demás.</p>
    <nav aria-label="Apartados de edición">{[["content", "Contenido"], ["conditions", "Condiciones"], ["requirements", "Requisitos"]].map(([key, title]) => <button type="button" disabled={busy} aria-pressed={section === key} key={key} onClick={() => setSection(key)}>{title}</button>)}</nav>
    <fieldset disabled={busy}>
      {section === "content" && <>
        <label>Cargo publicado<input className="field-control" maxLength={180} value={values.title} onChange={e => change("title", e.target.value)} /></label>
        <label>Funciones y descripción<textarea className="field-control" rows={8} maxLength={40000} value={values.description} onChange={e => change("description", e.target.value)} /></label>
        <label>Requisitos de la oferta<textarea className="field-control" rows={6} maxLength={20000} value={values.requirements} onChange={e => change("requirements", e.target.value)} /></label>
        <label>Sector<select className="field-control" value={values.sector || ""} onChange={e => change("sector", e.target.value || null)}><option value="">Sin especificar</option>{JOB_SECTORS.map(value => <option key={value}>{value}</option>)}</select></label>
        <label>Beneficios, uno por línea<textarea className="field-control" rows={3} value={values.benefits.join("\n")} onChange={e => change("benefits", e.target.value.split("\n"))} /></label>
        <div className="external-editor-grid">
          <label>Fecha original de publicación<input type="date" className="field-control" value={values.external_published_at?.slice(0, 10) || ""} onChange={e => change("external_published_at", e.target.value ? `${e.target.value}T00:00:00Z` : null)} /></label>

        </div><small>Usa la fecha original de publicación. La comprobación automática de vigencia se conserva por separado.</small>
      </>}
      {section === "conditions" && <>
        <h4>Remuneración publicada</h4><div className="external-editor-grid">
          <label>Salario mensual publicado en COP<CurrencyInput aria-label="Salario mensual publicado en COP" value={values.salary} onChange={v => { change("salary", v); quality("salary_currency", "COP"); quality("salary_period", "monthly"); }} /></label>
          <label>Salario máximo mensual en COP<CurrencyInput aria-label="Salario máximo mensual en COP" value={q.salary_max} onChange={v => quality("salary_max", v)} /></label>
        </div><label>Comisiones y remuneración variable<input className="field-control" maxLength={500} value={q.variable_pay || ""} onChange={e => quality("variable_pay", e.target.value)} /></label>
        <div className="external-editor-grid">
          <label>Modalidad<select className="field-control" value={values.modality || ""} onChange={e => change("modality", e.target.value)}><option value="" disabled>Sin especificar</option><option value="remote">Remoto</option><option value="hybrid">Híbrido</option><option value="onsite">Presencial</option></select></label>
          <label>Dedicación<select className="field-control" value={values.employment_type || ""} onChange={e => change("employment_type", e.target.value)}><option value="" disabled>Sin especificar</option>{Object.entries({ full_time: "Tiempo completo", part_time: "Tiempo parcial", contract: "Por contrato", internship: "Prácticas", temporary: "Temporal" }).map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label>
          <label>Tipo de contrato<select className="field-control" value={q.contract_type || ""} onChange={e => quality("contract_type", e.target.value)}>{Object.entries({ "": "Sin especificar", indefinite: "Indefinido", fixed_term: "Término fijo", services: "Prestación de servicios", apprenticeship: "Aprendizaje", project: "Obra o labor" }).map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label>
          <label>Ubicación publicada<input className="field-control" value={values.location || ""} maxLength={300} onChange={e => change("location", e.target.value || null)} /></label>
          <label>Departamento<input className="field-control" value={values.department || ""} maxLength={100} onChange={e => change("department", e.target.value || null)} /></label>
        </div>
        {values.modality === "remote" && <RemoteScopeEditor value={q.remote_scope} legacyLocation={values.location} onChange={v => quality("remote_scope", v)} />}
        <WorkScheduleEditor details={q} onChange={v => change("quality_details", v)} />
        <button type="button" className="button-secondary button-sm" onClick={() => change("quality_details", { ...q, schedule: "", work_schedule: null, weekly_hours: null })}>Dejar horario sin informar</button>
      </>}
      {section === "requirements" && <>
        <div className="external-editor-grid">
          <label>Experiencia mínima (meses)<input type="number" className="field-control" min={0} max={600} value={q.experience_months ?? (q.experience_years == null ? "" : q.experience_years * 12)} onChange={e => quality("experience_months", number(e.target.value))} /><small>0 indica sin experiencia; 12 meses equivalen a un año. Vacío significa sin informar.</small></label>
          <label>Nivel del cargo<select className="field-control" value={q.seniority || ""} onChange={e => quality("seniority", e.target.value)}>{Object.entries({ "": "Sin especificar", entry: "Inicial", junior: "Junior", mid: "Intermedio", senior: "Senior", lead: "Líder" }).map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label>
          <label>Formación exigida en la fuente<select className="field-control" value={values.required_education_level || ""} onChange={e => change("required_education_level", e.target.value || null)}><option value="">Sin requisito estructurado</option>{Object.entries(EDUCATION_LEVELS).map(([key, title]) => <option key={key} value={key}>{title}</option>)}</select></label>
          <label>Áreas de estudio, separadas por comas<input className="field-control" value={studyText} onChange={e => { setStudyText(e.target.value); change("required_study_fields", split(e.target.value)); }} /></label>
        </div>
        <label className="external-editor-check"><input type="checkbox" checked={!!q.education_accepts_in_progress} onChange={e => quality("education_accepts_in_progress", e.target.checked)} />La oferta acepta estudios en curso</label>
        <section><h4>Idiomas y niveles mínimos</h4><LanguagesEditor required value={values.languages} onChange={v => change("languages", v)} /></section>
        <section><h4>Habilidades solicitadas</h4><label>Habilidades, separadas por comas<input className="field-control" value={skillText} onChange={e => { setSkillText(e.target.value); change("skill_requirements", split(e.target.value).map(name => values.skill_requirements.find(row => row.skill === name) || { skill: name, essential: false, level: "unspecified", weight: 1 })); }} /></label>
          {values.skill_requirements.map((row, index) => <div className="external-editor-skill" key={index}><strong>{row.skill}</strong><label className="external-editor-check"><input type="checkbox" checked={!!row.essential} onChange={e => skill(index, "essential", e.target.checked)} />Indispensable</label><label>Nivel de {row.skill}<select className="field-control" value={row.level || "unspecified"} onChange={e => skill(index, "level", e.target.value)}>{Object.entries(levels).map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label></div>)}
        </section>
        <CredentialRequirementsEditor value={q.credential_requirements} onChange={v => quality("credential_requirements", v)} />
      </>}
    </fieldset>
    <label>Qué información contrastaste en la oferta original<textarea aria-label="Qué información contrastaste en la oferta original" className="field-control" rows={3} required minLength={10} maxLength={2000} value={note} onChange={e => setNote(e.target.value)} /><small>Solo se guardan los campos modificados. Puedes seguir completando la oferta después de guardar.</small></label>
    <footer><span>{Object.keys(changed).length ? `${Object.keys(changed).length} apartados con cambios` : "Sin cambios pendientes"}</span><button type="submit" className="button-primary" disabled={busy || !Object.keys(changed).length}>{busy ? "Guardando…" : "Guardar contenido"}</button></footer>
  </form>;
}
