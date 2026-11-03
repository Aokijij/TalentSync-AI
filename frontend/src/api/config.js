export const DEFAULT_API_URL = "/api/v1";

function isLocalHost(hostname = "") {
  return ["localhost", "127.0.0.1", "::1", "[::1]", "0.0.0.0"].includes(hostname.toLowerCase());
}

export function resolveApiBase(configuredValue, browserLocation = {}) {
  const configured = String(configuredValue || "").trim().replace(/\/$/, "");
  if (isLocalHost(browserLocation.hostname || "")) return configured || DEFAULT_API_URL;
  if (configured.startsWith("/") && !configured.startsWith("//")) return configured;
  try {
    const url = new URL(configured);
    if (url.protocol === "https:" && !isLocalHost(url.hostname) && !url.username && !url.password && !url.search && !url.hash) return configured;
  } catch { /* Empty or unsafe configuration stays on the application's origin. */ }
  return DEFAULT_API_URL;
}
