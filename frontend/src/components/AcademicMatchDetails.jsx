import { EDUCATION_LEVELS } from "../constants/educationLevels.js";

const STATUSES = { fulfilled: "Formación coincidente", partial: "Afinidad académica parcial", not_met: "Requisito académico sin cumplir", review: "Formación por revisar" };
const LEVELS = { meets: "Cumple el nivel", below: "Nivel inferior al solicitado", unknown: "Nivel por confirmar", in_progress: "En curso; se solicitan estudios terminados", not_required: "Sin nivel mínimo" };

export function AcademicMatchDetails({ value }) {
  if (!value || value.status === "not_required") return null;
  const row = value.selected;
  return <section className={`academic-match ${value.status}`} aria-label="Comparación de formación">
    <strong>{STATUSES[value.status] || "Comparación académica"}</strong><p>{value.reason}</p>
    {row && <dl><div><dt>Formación registrada</dt><dd>{row.candidate_degree || "Sin indicar"}</dd></div><div><dt>Área solicitada</dt><dd>{row.requested_field || "Sin restricción de área"}</dd></div><div><dt>Nivel académico</dt><dd>{EDUCATION_LEVELS[row.actual_level] || "Sin confirmar"}{value.required_level ? ` · solicitado: ${EDUCATION_LEVELS[value.required_level]}` : ""}</dd></div><div><dt>Resultado del nivel</dt><dd>{LEVELS[row.level_status]}</dd></div></dl>}
    <small>{row?.field_score != null && value.requested_fields?.length ? `Afinidad del área: ${row.field_score}/100. ` : ""}{row && value.required_level && row.level_status !== "unknown" ? `Cumplimiento del nivel: ${row.level_score}/100. ` : ""}{value.policy === "exact" ? "Se admiten las áreas seleccionadas y sus variantes de nombre." : "Una formación afín aporta cumplimiento parcial del área."} Declarar estudios no acredita un diploma.</small>
  </section>;
}
