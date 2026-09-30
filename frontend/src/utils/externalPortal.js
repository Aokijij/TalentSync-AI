const portals = [
  ["linkedin.", "LinkedIn"],
  ["computrabajo.", "Computrabajo"],
  ["elempleo.", "El Empleo"],
  ["indeed.", "Indeed"],
  ["glassdoor.", "Glassdoor"],
  ["magneto", "Magneto"],
  ["ticjob.", "Ticjob"],
  ["talent.com", "Talent.com"],
  ["jobrapido.", "Jobrapido"],
  ["bebee.", "BeBee"],
  ["ziprecruiter.", "ZipRecruiter"],
  ["workdayjobs.", "Workday"],
  ["greenhouse.io", "Greenhouse"],
  ["lever.co", "Lever"],
];

export function externalPortal(job) {
  if (job?.source_portal) return job.source_portal;
  try {
    const hostname = new URL(job?.external_url || "").hostname.toLowerCase();
    const match = portals.find(([fragment]) => hostname.includes(fragment));
    if (match) return match[1];
  } catch {
    // The API can return an empty URL while a listing is being refreshed.
  }
  const locationMatch = String(job?.location || "").match(
    /(?:a través de|via)\s+([^•,]+)/i,
  );
  return locationMatch?.[1]?.trim() || "el sitio de la empresa";
}
