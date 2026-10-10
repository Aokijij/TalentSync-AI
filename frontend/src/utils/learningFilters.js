export function filterResources(resources, { query = "", origin = "all", cost = "all", kind = "all", provider = "all", level = "all", language = "all" } = {}) {
  const fold = (value) => String(value).normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
  return resources.filter((row) => (origin === "all" || (origin === "external") === Boolean(row.url)) &&
    (cost === "all" || (row.cost || "free") === cost) && (kind === "all" || row.kind === kind) &&
    (provider === "all" || row.provider === provider) && (level === "all" || row.details?.level === level) &&
    (language === "all" || row.details?.languages?.includes(language)) &&
    fold([row.title, row.provider, ...(row.skills || [])].join(" ")).includes(fold(query)));
}
