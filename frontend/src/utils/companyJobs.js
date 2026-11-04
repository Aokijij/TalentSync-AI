import { skillKey } from "./skillLevels.js";

export const jobStateLabels = { active: "Publicada", draft: "Borrador", paused: "Pausada", closed: "Cerrada", filled: "Cubierta" };
export function companyJobCounts(jobs) {
  return { total: jobs.length, active: jobs.filter(job => job.status === "active").length,
    draft: jobs.filter(job => job.status === "draft").length, paused: jobs.filter(job => job.status === "paused").length,
    ready: jobs.filter(job => job.status === "draft" && job.quality_summary?.can_publish === true).length,
    incomplete: jobs.filter(job => job.status === "draft" && job.quality_summary?.can_publish !== true).length };
}
export function filterCompanyJobs(jobs, { query = "", status = "all", readiness = "all" } = {}) {
  const term = skillKey(query);
  return jobs.filter(job => (status === "all" || job.status === status)
    && (readiness === "all" || (job.quality_summary?.can_publish === true ? "ready" : "incomplete") === readiness)
    && (!term || skillKey([job.title, job.description, job.location, job.department, ...(job.skills || [])].filter(Boolean).join(" ")).includes(term)));
}
