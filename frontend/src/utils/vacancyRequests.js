// Each route owns its requests. A response from a previous vacancy cannot
// update the active screen, even when a transport ignores cancellation.
export function loadVacancyData(client, { jobId, role }, handlers) {
  const controller = new AbortController(); let active = true;
  const accept = (callback) => ({ data }) => { if (active) callback(data); };
  const fallback = (callback) => () => { if (active) callback(); };
  client.get(`/jobs/${jobId}`, { signal: controller.signal }).then(accept(handlers.job)).catch(fallback(handlers.error));
  client.get("/jobs", { signal: controller.signal }).then(accept(handlers.catalog)).catch(fallback(() => handlers.catalog([])));
  if (role === "candidate") {
    client.post(`/jobs/${jobId}/match`, {}, { signal: controller.signal, __quiet: true }).then(accept(handlers.match)).catch((failure) => { if (active && failure.code !== "ERR_CANCELED") { handlers.match(null); handlers.matchError?.(failure); } });
    client.get("/applications/me", { signal: controller.signal }).then(accept(handlers.applications)).catch(fallback(() => handlers.applications([])));
  }
  if (role === "company") client.get("/companies/me", { signal: controller.signal }).then(accept(handlers.company)).catch(fallback(() => handlers.company(null)));
  return () => { active = false; controller.abort(); };
}
