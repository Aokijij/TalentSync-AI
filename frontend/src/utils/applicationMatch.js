const finite = (value) => value == null || value === "" || !Number.isFinite(Number(value)) ? null : Number(value);
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

export function applicationBaseMatch(application) {
  return finite(application?.base_match_percentage);
}

export function answerAdjustment(answers = [], adjustments = {}) {
  const configured = answers.reduce((sum, row) => sum + (finite(row.configured_adjustment) ?? 0), 0);
  const manual = answers.filter((row) => row.type !== "choice").reduce((sum, row) => sum + (finite(adjustments[row.question_id] ?? row.reviewer_adjustment) ?? 0), 0);
  return clamp(configured + manual, -20, 20);
}

export function projectedMatch(base, adjustment) {
  const value = finite(base);
  return value == null ? null : clamp(value + (finite(adjustment) ?? 0), 0, 100);
}

export function mergeApplicationMatch(application, explanation) {
  const base = applicationBaseMatch(explanation);
  if (base == null) return application;
  return { ...application, base_match_percentage: base, adjusted_match_percentage: projectedMatch(base, application.screening_adjustment ?? explanation.screening_adjustment) };
}
