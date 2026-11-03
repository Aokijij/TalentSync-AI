import { EDUCATION_LEVELS } from "../constants/educationLevels.js";

const rank = { secondary: 0, technical: 1, technologist: 2, university: 3, postgraduate: 4 };
export function academicPresentation(value) {
  const row = value?.selected;
  if (!row) return { title: "Falta información académica", tone: "review", checks: [], summary: "Registra el título, el nivel y si el estudio está terminado para poder compararlo con la vacante." };
  const fieldRequired = Boolean(value.requested_fields?.length);
  const areaMeets = ["exact", "name_variant", "not_required"].includes(row.status);
  const areaPartial = row.status === "related";
  const areaUnknown = row.status === "review";
  const levelRequired = Boolean(value.required_level);
  const knownLevel = row.actual_level in rank;
  const levelMeets = !levelRequired || knownLevel && rank[row.actual_level] >= rank[value.required_level];
  const completionRequired = levelRequired && !value.accepts_in_progress;
  const completionMeets = !completionRequired || !row.in_progress;
  const checks = [
    { key: "area", label: "Área de formación", tone: !fieldRequired || areaMeets ? "met" : areaPartial ? "partial" : areaUnknown ? "review" : "unmet", result: !fieldRequired ? "Sin restricción de área" : areaMeets ? "Cumple el área" : areaPartial ? "Afinidad parcial" : areaUnknown ? "Nombre por revisar" : "No cumple el área", requested: fieldRequired ? row.requested_field || value.requested_fields.join(" o ") : "Cualquier área", actual: row.candidate_degree || "Sin título registrado", explanation: !fieldRequired ? "La oferta no limita las carreras o áreas aceptadas." : areaMeets ? "El título coincide con un área admitida, aunque su nombre pueda tener una variante." : areaPartial ? "Es un área relacionada que la empresa admite parcialmente; no equivale al título solicitado." : areaUnknown ? "El nombre no se reconoce con suficiente certeza. Hace falta revisar el contenido del estudio." : "El área registrada no está entre las alternativas admitidas por esta oferta." },
    { key: "level", label: "Nivel académico", tone: levelMeets ? "met" : knownLevel ? "unmet" : "review", result: !levelRequired ? "Sin nivel mínimo" : levelMeets ? "Cumple el nivel" : knownLevel ? "Nivel inferior al solicitado" : "Nivel sin indicar", requested: EDUCATION_LEVELS[value.required_level] || "Sin mínimo", actual: EDUCATION_LEVELS[row.actual_level] || "Sin indicar", explanation: !levelRequired ? "No se solicita un nivel académico mínimo." : levelMeets ? "El nivel del estudio es igual o superior al mínimo. Su finalización se revisa por separado." : knownLevel ? "El nivel registrado es inferior al mínimo de la oferta." : "Falta indicar el nivel del estudio para confirmar este punto." },
    { key: "completion", label: "Finalización del estudio", tone: completionMeets ? "met" : "unmet", result: !levelRequired ? "Sin restricción de finalización" : row.in_progress ? value.accepts_in_progress ? "Estudios en curso aceptados" : "Falta terminar el estudio" : "Estudio terminado declarado", requested: !levelRequired ? "Sin condición adicional" : value.accepts_in_progress ? "Terminado o en curso" : "Estudios terminados", actual: row.in_progress ? "En curso" : "Terminado (declarado)", explanation: !levelRequired ? "La oferta no exige un estudio finalizado de un nivel concreto." : !completionMeets ? "El estudio continúa en curso y esta oferta solicita que esté terminado." : row.in_progress ? "La empresa acepta expresamente personas que todavía están estudiando." : "La formación no figura como estudio actual. El diploma se comprueba durante la contratación." },
  ];
  const unmet = checks.filter((check) => check.tone === "unmet"), pending = checks.some((check) => check.tone === "review");
  const complete = checks.every((check) => check.tone === "met");
  return { checks, tone: complete ? "fulfilled" : pending ? "review" : "partial", title: complete ? "Cumple la formación declarada" : !completionMeets && areaMeets && levelMeets ? "Coincide la formación; falta finalizarla" : pending ? "Formación pendiente de confirmar" : "Hay condiciones académicas sin cumplir", summary: complete ? "El mismo estudio cumple el área, el nivel y la condición de finalización solicitados." : unmet.length ? unmet.map((check) => check.explanation).join(" ") : pending ? "Hay datos que necesitan revisión antes de confirmar el requisito." : "El área es afín, pero no una coincidencia completa con la formación solicitada." };
}
