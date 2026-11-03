import { processDate } from "./interviewAgenda.js";
import { isProcessClosed } from "./recruitmentState.js";

export function responseState(row, now = new Date()) {
  if (isProcessClosed(row)) return "closed";
  if (row.response_paused_at || row.response_state === "paused") return "paused";
  const due = processDate(row.response_due_at);
  if (due) return due <= now ? "overdue" : "on_time";
  return row.response_state || "none";
}

export const responseLabels = { overdue: "Respuesta atrasada", paused: "En pausa · Falta de respuesta de la empresa", on_time: "Respuesta comprometida", none: "Sin compromiso de respuesta", closed: "Proceso finalizado" };
export const responseTime = (value) => processDate(value)?.toLocaleString("es-CO", { timeZone: "America/Bogota", dateStyle: "medium", timeStyle: "short" }) || "Por confirmar";

export function proposedResponseDate(dueAt, now = new Date()) {
  const due = processDate(dueAt);
  const next = new Date(Math.max(now.getTime(), due?.getTime() || 0));
  const weekday = new Intl.DateTimeFormat("en-US", { timeZone: "America/Bogota", weekday: "short" });
  next.setUTCDate(next.getUTCDate() + 1);
  while (["Sat", "Sun"].includes(weekday.format(next))) next.setUTCDate(next.getUTCDate() + 1);
  return next.toISOString();
}
