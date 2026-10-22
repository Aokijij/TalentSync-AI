import { timestamp } from "./dashboardData.js";

export function practiceSeconds(expiresAt, now = Date.now()) {
  const end = timestamp(expiresAt);
  return Number.isFinite(end) ? Math.max(0, Math.ceil((end - now) / 1000)) : 0;
}

export function practiceDraft(value, questions) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const result = {};
  for (const item of questions) {
    const answer = value[item.id], choices = item.choices || [];
    if (item.type === "number") {
      if ((typeof answer === "string" || typeof answer === "number") && String(answer).trim() !== "" && Number.isFinite(Number(answer))) result[item.id] = answer;
    } else if (["order", "matching", "multi_select"].includes(item.type)) {
      if (Array.isArray(answer) && (item.type === "matching" || new Set(answer).size === answer.length) && answer.every((index) => Number.isInteger(index) && index >= (item.type === "matching" ? -1 : 0) && index < choices.length)
          && (item.type === "multi_select" || answer.length === (item.terms?.length || choices.length))) result[item.id] = answer;
    } else if (Number.isInteger(answer) && answer >= 0 && answer < choices.length) result[item.id] = answer;
  }
  return result;
}

export function restorePractice(storage, key, questions) {
  try {
    const draft = JSON.parse(storage.getItem(key) || "{}");
    if (!draft || typeof draft !== "object" || Array.isArray(draft)) throw new Error("Invalid draft");
    return { answers: practiceDraft(draft, questions), warning: "" };
  } catch {
    return { answers: {}, warning: "No pudimos recuperar el borrador de este navegador. Mantén abierta la práctica para conservar tus respuestas actuales." };
  }
}

export function savePractice(storage, key, answers) {
  try { storage.setItem(key, JSON.stringify(answers)); return ""; }
  catch { return "El navegador no permite guardar el borrador. Tus respuestas siguen en esta pantalla; entrégalas antes de salir."; }
}

export const questionInstruction = (type) => ({ number: "Escribe el resultado del cálculo.", order: "Ordena los pasos y confirma tu selección.", matching: "Relaciona cada concepto con su función.", multi_select: "Selecciona todas las opciones que correspondan." }[type] || "Selecciona una respuesta para continuar.");
