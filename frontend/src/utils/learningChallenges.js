import { timestamp } from "./dashboardData.js";
export function latestChallengeAttempt(row, localAttempt) {
  const saved = row.last_attempt;
  if (localAttempt?.assessment_id !== row.id) return saved;
  if (!saved) return localAttempt;
  if (saved.id === localAttempt.id) {
    if (Number(saved.version || 0) > Number(localAttempt.version || 0)) return saved;
    if (saved.status === "completed" && localAttempt.status === "active") return saved;
    return localAttempt;
  }
  return timestamp(localAttempt.started_at) > timestamp(saved.started_at) ? localAttempt : saved;
}
export function challengeState(row, now = Date.now()) {
  const last = row.last_attempt;
  const active = last?.status === "active" && timestamp(last.expires_at) > now;
  const retryAt = timestamp(last?.started_at) + 86400000;
  const waiting = !active && retryAt > now;
  return { active, waiting, retryAt, completed: last?.status === "completed", passed: Boolean(last?.passed), label: active ? "Continuar práctica" : waiting ? "Disponible después" : last ? "Volver a practicar" : "Empezar práctica" };
}
