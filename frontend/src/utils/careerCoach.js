export function buildStarDraft({ situation = "", task = "", action = "", result = "" }) {
  const facts = [situation, task, action, result].map((value) => value.trim());
  if (facts.some((value) => !value || /\[[^\]]+\]/.test(value))) return "";
  const draft = facts.map((value) => /[.!?]$/.test(value) ? value : `${value}.`).join(" ");
  return draft.length <= 3000 ? draft : "";
}
