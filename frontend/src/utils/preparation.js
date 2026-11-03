export const starFields = [["situation", "Contexto", "¿Qué estaba pasando?"], ["task", "Responsabilidad", "¿Qué te correspondía hacer?"], ["action", "Acción", "¿Qué hiciste tú y cómo lo hiciste?"], ["result", "Resultado", "¿Qué entregaste, cambió o aprendiste?"]];

export function reviewAnswer(answer = {}) {
  const missing = starFields.filter(([key]) => !String(answer[key] || "").trim()).map(([, label]) => label);
  return { complete: missing.length === 0, missing };
}

export function preparationText(job, questions, answers) {
  return [`Preparación privada · ${job.title}`, job.company_name, "", ...questions.flatMap((question) => [question.title, ...starFields.map(([key, label]) => `${label}: ${answers[question.id]?.[key] || ""}`), ""])].join("\n");
}

export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; document.body.append(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}
