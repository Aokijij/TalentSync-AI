import { JOB_SECTORS } from "../constants/jobSectors.js";

export const CONTRACTS = { indefinite: "Indefinido", fixed_term: "Término fijo", services: "Prestación de servicios", apprenticeship: "Aprendizaje", project: "Obra o labor" };
export const LEVELS = { entry: "Inicial / sin experiencia", junior: "Junior", mid: "Intermedio", senior: "Senior", lead: "Liderazgo" };
export const QUALITY_STEPS = ["Condiciones", "Responsabilidades", "Requisitos", "Proceso", "Revisar y publicar"];
export const EMPTY_DETAILS = { version: 1, salary_currency: "COP", salary_period: "monthly", salary_basis: "gross_base", weekly_hours: null, salary_max: null, variable_pay: "", contract_type: "", schedule: "", seniority: "", experience_years: null, learnable_skills: [], missions: [], interview_count: null, process_days: null };

export function offerDraft(job = {}) {
  return { title: "", description: "", requirements: "", salary: null, location: "", department: "", modality: "remote", employment_type: "full_time", sector: JOB_SECTORS[0], benefits: [], languages: [], application_questions: [], required_education_level: null, required_study_fields: [], response_days: 7, blind_hiring: true, status: "draft", ...job,
    skill_requirements: job.skill_requirements?.length ? job.skill_requirements.map((row) => ({ ...row })) : (job.skills || []).map((skill) => ({ skill, essential: false, weight: 1 })),
    quality_details: { ...EMPTY_DETAILS, ...job.quality_details, missions: (job.quality_details?.missions || []).map((row) => ({ ...row })) } };
}

export function offerPayload(draft) {
  const payload = {};
  for (const key of ["title", "description", "requirements", "location", "department", "modality", "employment_type", "sector", "languages", "benefits", "response_days", "blind_hiring", "skill_requirements", "quality_details", "application_questions", "required_education_level", "required_study_fields"]) payload[key] = draft[key];
  payload.required_education_level = draft.required_education_level || null;
  payload.required_study_fields = typeof draft.required_study_fields === "string" ? draft.required_study_fields.split(",").map((value) => value.trim()).filter(Boolean) : draft.required_study_fields || [];
  payload.salary = draft.salary === "" || draft.salary == null ? null : Number(draft.salary);
  payload.response_days = Number(draft.response_days) || 7;
  payload.skill_requirements = (draft.skill_requirements || []).filter((row) => row.skill.trim()).map((row) => ({ ...row, skill: row.skill.trim(), weight: Number(row.weight) || 1 }));
  payload.quality_details = { ...draft.quality_details,
    // The publisher reviews these units in the guided salary fields.
    salary_currency: "COP", salary_period: "monthly", salary_basis: "gross_base",
    weekly_hours: draft.quality_details.weekly_hours === "" || draft.quality_details.weekly_hours == null ? null : Number(draft.quality_details.weekly_hours),
    salary_max: draft.quality_details.salary_max === "" || draft.quality_details.salary_max == null ? null : Number(draft.quality_details.salary_max),
    missions: draft.quality_details.missions.map((row) => ({ ...row, days: Number(row.days) || 90 })) };
  return payload;
}

export function salaryLabel(job) {
  if (!job.salary) return "Salario no informado";
  const min = `$${Number(job.salary).toLocaleString("es-CO")}`;
  const max = job.quality_details?.salary_max;
  return max && max > job.salary ? `${min} – $${Number(max).toLocaleString("es-CO")} COP / mes` : `${min} COP / mes`;
}
