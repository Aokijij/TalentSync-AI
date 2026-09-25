export const PRODUCTION_API_URL =
  "https://talentsync-3c02d6e1.yellowwater-01e17d41.eastus2.azurecontainerapps.io/api/v1";

const LOCAL_API_URL = "/api/v1";

function isLocalHost(hostname = "") {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

function isLocalApi(value = "") {
  try {
    return isLocalHost(new URL(value).hostname);
  } catch {
    return false;
  }
}

export function resolveApiBase(configuredValue, browserLocation = {}) {
  const configured = String(configuredValue || "").trim().replace(/\/$/, "");
  const hostname = String(browserLocation.hostname || "").toLowerCase();

  if (isLocalHost(hostname)) return configured || LOCAL_API_URL;
  if (configured && !configured.startsWith("/") && !isLocalApi(configured)) {
    return configured;
  }
  if (hostname.endsWith(".azurecontainerapps.io") && configured.startsWith("/")) {
    return configured;
  }

  // A static production build must never try to call the visitor's computer.
  // This fallback also protects a Pages deployment built without its variable.
  return PRODUCTION_API_URL;
}
