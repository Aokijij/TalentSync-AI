export const WORK_DAYS = [["mon", "Lunes", "L"], ["tue", "Martes", "M"], ["wed", "Miércoles", "X"], ["thu", "Jueves", "J"], ["fri", "Viernes", "V"], ["sat", "Sábado", "S"], ["sun", "Domingo", "D"]];
export const EMPTY_WORK_SCHEDULE = { mode: "fixed", days: [], start: "", end: "", break_minutes: 0, notes: "" };
const minutes = (value) => /^([01]\d|2[0-3]):[0-5]\d$/.test(value) ? Number(value.slice(0, 2)) * 60 + Number(value.slice(3)) : null;

export function orderedDays(days = []) { return WORK_DAYS.filter(([key]) => days.includes(key)); }
export function scheduleHours(value) {
  const start = minutes(value.start), end = minutes(value.end);
  if (value.mode !== "fixed" || start == null || end == null || start === end || !orderedDays(value.days).length) return null;
  const duration = (end - start + 1440) % 1440 - Number(value.break_minutes || 0);
  if (duration <= 0) return null;
  return Math.round(duration * orderedDays(value.days).length / 60 * 100) / 100;
}

export function scheduleSummary(value) {
  const days = orderedDays(value.days), keys = days.map(([key]) => key).join(",");
  const dayText = ({ "mon,tue,wed,thu,fri": "Lunes a viernes", "mon,tue,wed,thu,fri,sat": "Lunes a sábado", "sat,sun": "Sábados y domingos", "mon,tue,wed,thu,fri,sat,sun": "Lunes a domingo" })[keys] || days.map(([, label]) => label).join(", ");
  const parts = [];
  if (value.mode === "flexible") parts.push("Horario flexible");
  if (value.mode === "rotating") parts.push("Turnos rotativos");
  if (dayText) parts.push(dayText);
  if (value.mode === "fixed" && minutes(value.start) != null && minutes(value.end) != null && value.start !== value.end) {
    parts.push(`${value.start} a ${value.end}${value.end < value.start ? " (finaliza al día siguiente)" : ""}`);
    if (Number(value.break_minutes) > 0) parts.push(`${value.break_minutes} minutos de descanso`);
  }
  if (value.notes?.trim()) parts.push(value.notes.trim());
  return parts.join(" · ");
}
