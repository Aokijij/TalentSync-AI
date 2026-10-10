import { courseAvailability } from "./learningPresentation.js";

export function filterResources(resources, { query = "", origin = "all", cost = "all", kind = "all", provider = "all", level = "all", language = "all", enrollment = "all", modality = "all", certificate = "all" } = {}) {
  const fold = (value) => String(value).normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
  return resources.filter((row) => (origin === "all" || (origin === "external") === Boolean(row.url)) &&
    (cost === "all" || (row.cost || "free") === cost) && (kind === "all" || row.kind === kind) &&
    (provider === "all" || row.provider === provider) && (level === "all" || row.details?.level === level) &&
    (language === "all" || row.details?.languages?.includes(language)) &&
    (enrollment === "all" || courseAvailability(row).status === enrollment) &&
    (modality === "all" || courseAvailability(row).modality === modality) &&
    (certificate === "all" || row.details?.certificate_cost === certificate) &&
    fold([row.title, row.provider, ...(row.skills || [])].join(" ")).includes(fold(query)));
}
