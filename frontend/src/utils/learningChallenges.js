import { timestamp } from "./dashboardData.js";
export function challengeState(row, now = Date.now()) {
  const last = row.last_attempt;
  const active = last?.status === "active" && timestamp(last.expires_at) > now;
  const retryAt = timestamp(last?.started_at) + 86400000;
  const waiting = !active && retryAt > now;
  return { active, waiting, retryAt, completed: last?.status === "completed", passed: Boolean(last?.passed), label: active ? "Continuar práctica" : waiting ? "Disponible después" : last ? "Volver a practicar" : "Empezar práctica" };
}
