export function minimumExperienceMonths(details = {}) {
  if (details.experience_months != null && details.experience_months !== "") return Number(details.experience_months);
  return details.experience_years == null || details.experience_years === "" ? null : Number(details.experience_years) * 12;
}
export function experienceLabel(details = {}) {
  const months = minimumExperienceMonths(details);
  if (months == null) return "Experiencia por definir";
  if (!months) return "Sin experiencia previa";
  const years = Math.floor(months / 12), rest = months % 12;
  return [years ? `${years} ${years === 1 ? "año" : "años"}` : "", rest ? `${rest} ${rest === 1 ? "mes" : "meses"}` : ""].filter(Boolean).join(" y ");
}
