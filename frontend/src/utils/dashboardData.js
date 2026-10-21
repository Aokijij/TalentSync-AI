const closed = new Set(["rejected", "accepted", "hired"]);
export const isOpenProcess = (row) => !closed.has(row.status) && !row.released_at;
export function timestamp(value) {
  if (typeof value === "number") return value;
  if (!value) return NaN;
  const text = String(value);
  return Date.parse(text.includes("T") && !/(?:Z|[+-]\d{2}:\d{2})$/i.test(text) ? `${text}Z` : text);
}
export const applicationLabels = { submitted: "Recibida", seen: "Recibida", reviewing: "En revisión", shortlisted: "En revisión", technical_interview: "Entrevista", psychometric_test: "Entrevista", accepted: "Seleccionado", hired: "Contratado", rejected: "No seleccionado" };
export function dashboardDate(value, includeTime = true) {
  const time = timestamp(value);
  return Number.isFinite(time) ? new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", ...(includeTime ? { hour: "numeric", minute: "2-digit" } : {}) }).format(time) : "Fecha por confirmar";
}
export function processOverview(applications, now = Date.now()) {
  const active = applications.filter(isOpenProcess);
  return {
    active,
    pending: active.filter((row) => ["submitted", "seen"].includes(row.status)),
    urgent: active.filter((row) => timestamp(row.response_due_at) <= now + 86400000).sort((a, b) => timestamp(a.response_due_at) - timestamp(b.response_due_at)),
    interviews: active.filter((row) => timestamp(row.interview_at) >= now).sort((a, b) => timestamp(a.interview_at) - timestamp(b.interview_at)),
    recent: [...applications].sort((a, b) => (timestamp(b.created_at) || 0) - (timestamp(a.created_at) || 0)).slice(0, 5),
    selected: applications.filter((row) => ["accepted", "hired"].includes(row.status)).length,
  };
}

export function candidateOpportunities(recommendations, jobs, applications, now = Date.now()) {
  const applied = new Set(applications.map((row) => row.job_id));
  const byId = new Map(jobs.map((job) => [job.id, job]));
  return recommendations.filter((row) => {
    const job = byId.get(row.job_id);
    return job && (!job.status || job.status === "active") && (!job.expires_at || timestamp(job.expires_at) > now) && !applied.has(row.job_id);
  }).sort((a, b) => b.match_percentage - a.match_percentage);
}

export function companyOpportunities(jobs, applications, now = Date.now()) {
  const counts = new Map();
  applications.forEach((row) => counts.set(row.job_id, (counts.get(row.job_id) || 0) + 1));
  const active = jobs.filter((job) => job.status === "active" && (!job.expires_at || timestamp(job.expires_at) > now));
  return { active, drafts: jobs.filter((job) => job.status === "draft"), quiet: active.filter((job) => !counts.has(job.id)), counts };
}
