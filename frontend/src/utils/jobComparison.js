import { CONTRACTS } from "./offerQuality.js";
import { experienceLabel } from "./jobRequirements.js";
import { remoteScopeLabels } from "./remoteScope.js";
import { scheduleSummary } from "./workSchedule.js";
import { EDUCATION_LEVELS } from "../constants/educationLevels.js";
import { languageLevelLabel } from "../constants/languages.js";

export const COMPARISON_LIMIT = 3;

export function comparisonIds(value) {
  try {
    const ids = typeof value === "string" ? JSON.parse(value) : value;
    return Array.isArray(ids) ? [...new Set(ids.filter((id) => Number.isSafeInteger(id) && id > 0))].slice(0, COMPARISON_LIMIT) : [];
  } catch { return []; }
}

export function toggleComparedJob(ids, id) {
  const current = comparisonIds(ids);
  if (current.includes(id)) return current.filter((value) => value !== id);
  return Number.isSafeInteger(id) && id > 0 && current.length < COMPARISON_LIMIT ? [...current, id] : current;
}

export function comparisonSalary(job) {
  if (!(Number(job.salary) > 0)) return "Salario no informado";
  const details = job.quality_details || {};
  const range = [job.salary, details.salary_max > job.salary ? details.salary_max : null].filter((value) => value != null).map((value) => Number(value).toLocaleString("es-CO")).join(" – ");
  const currency = details.salary_currency || (job.source_kind === "external" ? null : "COP");
  const period = { monthly: "mes", yearly: "año", hourly: "hora" }[details.salary_period] || (job.source_kind === "external" ? null : "mes");
  return `${range} ${currency || "(moneda por confirmar)"}${period ? ` / ${period}` : " · período por confirmar"}`;
}

export function comparisonFacts(job) {
  const details = job.quality_details || {};
  return {
    salary: comparisonSalary(job),
    modality: { remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" }[job.modality] || "Sin especificar",
    location: job.modality === "remote" && details.remote_scope ? remoteScopeLabels(details.remote_scope).join(" · ") : [job.location, job.department].filter(Boolean).join(", ") || "Sin especificar",
    contract: CONTRACTS[details.contract_type] || "Contrato sin especificar",
    schedule: [details.work_schedule ? scheduleSummary(details.work_schedule) : details.schedule, details.weekly_hours != null ? `${details.weekly_hours} horas semanales` : ""].filter(Boolean).join(" · ") || "Horario sin especificar",
    experience: experienceLabel(details),
    education: [EDUCATION_LEVELS[job.required_education_level], ...(job.required_study_fields || []), job.required_education_level && details.education_accepts_in_progress ? "Admite estudios en curso" : ""].filter(Boolean).join(" · ") || "Formación sin especificar",
    languages: (job.languages || []).map((item) => `${item.name} · ${languageLevelLabel(item.level)}`).join(", ") || "Idiomas sin especificar",
    benefits: (job.benefits || []).join(" · ") || "Beneficios sin especificar",
    process: [details.process_days != null ? `${details.process_days} días estimados de selección` : "", job.source_kind !== "external" && job.response_days != null ? `${job.response_days} días laborables para responder a cada avance` : ""].filter(Boolean).join(" · ") || "Plazos sin especificar",
  };
}

export function comparisonRequirements(match) {
  const rows = match?.match_details?.requirements;
  if (!Array.isArray(rows)) return null;
  return { covered: rows.filter((row) => row.covered === true), pending: rows.filter((row) => row.covered !== true) };
}
