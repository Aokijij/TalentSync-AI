export const learningLevels = { beginner: "Inicial", intermediate: "Intermedio", advanced: "Avanzado", any: "Consultar nivel" };
export const certificateCosts = { free: "Certificado sin coste adicional", paid: "Certificado o examen de pago", conditional: "Certificación sujeta a condiciones", none: "Sin certificación anunciada", unknown: "Certificado por confirmar" };
export const enrollmentStatuses = { unknown: "Inscripción por confirmar", open: "Inscripción anunciada", closed: "Inscripciones cerradas", ongoing: "Acceso continuo anunciado" };
export const courseModalities = { virtual: "Virtual", onsite: "Presencial", hybrid: "Híbrida", distance: "A distancia", unknown: "Consultar modalidad" };

export function courseAvailability(resource, today = new Date().toISOString().slice(0, 10)) {
  const value = resource.availability || resource.details?.enrollment || {};
  const age = value.checked_on ? (Date.parse(today) - Date.parse(value.checked_on)) / 86400000 : Infinity;
  const stale = !Number.isFinite(age) || age < 0 || age > 14;
  const status = stale || value.unavailable || value.opens_on > today ? "unknown" : value.closes_on && value.closes_on < today ? "closed" : value.status || "unknown";
  return { ...value, status, stale };
}
export function learningLanguages(codes = []) {
  const names = { es: "Español", en: "Inglés", pt: "Portugués", fr: "Francés", de: "Alemán" };
  return codes.map((code) => names[code] || code).join(" · ");
}

export function formatLearningHours(value) {
  const hours = Number(value);
  if (!Number.isFinite(hours) || hours <= 0) return "Por confirmar";
  return hours < 0.05 ? "< 0.1" : String(Math.round(hours * 10) / 10);
}
