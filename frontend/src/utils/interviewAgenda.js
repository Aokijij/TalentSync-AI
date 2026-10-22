export const FINAL_PROCESS_STATUSES = new Set(["rejected", "accepted", "hired"]);

// API datetimes without offsets are UTC, never the device's local timezone.
export function processDate(value) {
  if (typeof value !== "string" || !value.trim()) return null;
  const parsed = new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
  return Number.isFinite(parsed.getTime()) ? parsed : null;
}

export function activeInterview(row, now = new Date()) {
  const date = processDate(row.interview_at);
  return !row.released_at && !FINAL_PROCESS_STATUSES.has(row.status) && date != null && date > now;
}

export function upcomingInterviews(applications, now = new Date()) {
  return applications.filter((row) => activeInterview(row, now)).sort((first, second) => processDate(first.interview_at) - processDate(second.interview_at));
}

export function interviewDateParts(value) {
  const date = processDate(value);
  if (!date) return null;
  const options = { timeZone: "America/Bogota" };
  return {
    day: date.toLocaleDateString("es-CO", { ...options, day: "2-digit" }),
    month: date.toLocaleDateString("es-CO", { ...options, month: "short" }),
    full: date.toLocaleDateString("es-CO", { ...options, weekday: "long", day: "numeric", month: "long", year: "numeric" }),
    time: date.toLocaleTimeString("es-CO", { ...options, hour: "2-digit", minute: "2-digit" }),
  };
}

export function interviewInputValue(value) {
  const date = processDate(value);
  if (!date) return "";
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-CA", { timeZone: "America/Bogota", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(date).map((part) => [part.type, part.value]));
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

export function interviewInputUtc(value) {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value || "")) return null;
  const date = processDate(`${value}:00-05:00`);
  return date && interviewInputValue(date.toISOString()) === value ? date.toISOString() : null;
}
