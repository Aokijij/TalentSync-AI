import { REMOTE_COUNTRIES, REMOTE_CONTINENTS } from "../constants/remoteLocations.js";
import { COLOMBIA_LOCATIONS } from "../constants/colombianCities.js";
const fold = (value) => String(value || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();
const colombianCities = new Set(Object.values(COLOMBIA_LOCATIONS).flat().map(fold));
export function remoteScopeFromLegacy(location = "") {
  const country = REMOTE_COUNTRIES.find((row) => [row.code, row.name, row.english_name].some((name) => fold(name) === fold(location)));
  if (country) return { mode: "regions", countries: [country.code], continents: [] };
  if (colombianCities.has(fold(location.split(",")[0]))) return { mode: "regions", countries: ["CO"], continents: [] };
  return { mode: "global", countries: [], continents: [] };
}
export function remoteScopeLabels(scope) {
  if (!scope || scope.mode === "global") return ["Desde cualquier país"];
  return [...(scope.continents || []).map((code) => REMOTE_CONTINENTS[code]).filter(Boolean), ...(scope.countries || []).map((code) => REMOTE_COUNTRIES.find((row) => row.code === code)?.name).filter(Boolean)];
}
export function remoteLocationLabel(scope) {
  const labels = remoteScopeLabels(scope), text = labels.join(", ");
  return text.length <= 120 ? text : `Remoto · ${scope.countries.length} países y ${scope.continents.length} continentes`;
}
