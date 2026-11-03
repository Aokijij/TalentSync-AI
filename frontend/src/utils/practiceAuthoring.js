export function practiceEditorValue(binding) {
  const draft = binding?.draft || {};
  return { mode: binding?.mode || "none", template_id: binding?.template_id || "", level: binding?.level || "beginner", rationale: binding?.rationale || "", title: draft.title || "", scenario: draft.scenario || "", steps: (draft.steps || []).join("\n"), calculation_prompt: draft.calculation_prompt || "", calculation_answer: draft.calculation_answer ?? "", calculation_feedback: draft.calculation_feedback || "", terms: (draft.terms || []).join("\n"), meanings: (draft.meanings || []).join("\n") };
}
const lines = (value) => value.split("\n").map((item) => item.trim()).filter(Boolean);
export function practiceBindingPayload(value) {
  if (value.mode === "none") return { mode: "none" };
  if (value.mode === "template") return { mode: "template", template_id: value.template_id, level: value.level, rationale: value.rationale.trim() };
  return { mode: "custom", rationale: value.rationale.trim(), draft: { title: value.title.trim(), scenario: value.scenario.trim(), steps: lines(value.steps), calculation_prompt: value.calculation_prompt.trim(), calculation_answer: Number(value.calculation_answer), calculation_feedback: value.calculation_feedback.trim(), terms: lines(value.terms), meanings: lines(value.meanings) } };
}
