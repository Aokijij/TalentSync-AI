export const learningLevels = { beginner: "Inicial", intermediate: "Intermedio", advanced: "Avanzado", any: "Consultar nivel" };
export const certificateCosts = { free: "Certificado sin coste adicional", paid: "Certificado o examen de pago", conditional: "Opciones gratuitas y de pago", none: "Sin certificación anunciada", unknown: "Certificado por confirmar" };
export function learningLanguages(codes = []) {
  const names = { es: "Español", en: "Inglés", pt: "Portugués", fr: "Francés", de: "Alemán" };
  return codes.map((code) => names[code] || code).join(" · ");
}
