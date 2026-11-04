export function isJobPublished(job) {
  return job?.status === "active" && job.moderation_status !== "held" && (job.source_kind !== "external" || job.external_available === true);
}
