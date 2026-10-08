const folded = (text) => String(text || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();

export function searchJob(job, query) {
  const text = folded([job.title, job.company_name, job.location, job.sector, job.modality, job.description, job.requirements, ...(job.skills || [])].join(" "));
  return folded(query).trim().split(/\s+/).every((term) => text.includes(term));
}

export function visibleInterest(job, byId, mode = "all") {
  const state = byId.get(job.id);
  return mode === "saved" ? state === true : mode === "hidden" ? state === false : state !== false;
}

export function meetsRequiredPreferences(recommendation, respect = true) {
  return !respect || !(recommendation.match_details?.preferences?.unmet_conditions?.length);
}
