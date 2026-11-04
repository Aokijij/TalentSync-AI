const channel = "talentsync:vacancy-updated";

// Only identifiers cross tabs. Vacancy content stays in authenticated API calls.
export function notifyVacancyMutation(config, surface = window) {
  if (!["patch", "put", "delete", "post"].includes(String(config?.method || "").toLowerCase())) return;
  const match = String(config?.url || "").match(/^\/(?:admin\/)?jobs\/(\d+)(?:\/(?:content|catalog-status|review|availability\/check))?$/);
  if (!match) return;
  const detail = { id: Number(match[1]), changedAt: Date.now(), nonce: Math.random() };
  surface.dispatchEvent(new CustomEvent(channel, { detail }));
  try { surface.localStorage.setItem(channel, JSON.stringify(detail)); } catch { /* Private browsing can disable storage. */ }
}

export function subscribeVacancyChanges(jobId, refresh, surface = window) {
  const receive = (event) => {
    let detail;
    try { detail = event.type === "storage" ? event.key === channel && JSON.parse(event.newValue) : event.detail; } catch { return; }
    if (Number(detail?.id) === Number(jobId)) refresh();
  };
  surface.addEventListener(channel, receive);
  surface.addEventListener("storage", receive);
  return () => { surface.removeEventListener(channel, receive); surface.removeEventListener("storage", receive); };
}
