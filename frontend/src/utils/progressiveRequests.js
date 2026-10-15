import { createPendingLoader } from "./pendingRequests.js";

// Keep account data only while a mounted view is listening or a request runs.
export function createProgressiveLoader(request, pause = () => new Promise((resolve) => setTimeout(resolve, 250))) {
  const pendingBatch = createPendingLoader(request);
  let generation = 0;
  const observers = new Map();
  const refreshing = new Map();

  function publish(accountId, response) {
    for (const observer of observers.get(String(accountId)) || []) {
      observer(response.data.items, response.data.pending > 0, null);
    }
  }
  function continueRefresh(accountId) {
    const key = String(accountId);
    if (refreshing.has(key) || !observers.get(key)?.size) return;
    const run = { stopped: false };
    refreshing.set(key, run);
    (async () => {
      try {
        while (!run.stopped && observers.get(key)?.size) {
          await pause();
          if (run.stopped || !observers.get(key)?.size) break;
          const response = await pendingBatch(accountId);
          if (run.stopped) break;
          publish(accountId, response);
          if (!response.data.pending) break;
        }
      } catch (error) {
        if (!run.stopped && error.code !== "ERR_CANCELED") {
          for (const observer of observers.get(key) || []) observer(null, false, error);
        }
      } finally {
        if (refreshing.get(key) === run) refreshing.delete(key);
      }
    })();
  }
  async function load(accountId) {
    const revision = generation;
    const response = await pendingBatch(accountId);
    if (revision !== generation) throw Object.assign(new Error("Solicitud cancelada"), { code: "ERR_CANCELED" });
    publish(accountId, response);
    if (response.data.pending) continueRefresh(accountId);
    return { ...response, data: response.data.items };
  }
  function subscribe(accountId, observer) {
    const key = String(accountId);
    if (!observers.has(key)) observers.set(key, new Set());
    observers.get(key).add(observer);
    return () => {
      observers.get(key)?.delete(observer);
      if (!observers.get(key)?.size) {
        observers.delete(key);
        const run = refreshing.get(key);
        if (run) { run.stopped = true; refreshing.delete(key); }
      }
    };
  }
  function cancel() {
    generation += 1;
    pendingBatch.clear();
    for (const run of refreshing.values()) run.stopped = true;
    refreshing.clear();
  }
  return { load, subscribe, cancel };
}
