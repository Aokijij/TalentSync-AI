// Share only requests that are currently running; never retain account data.
export function createPendingLoader(request) {
  const pending = new Map();
  const load = (accountId) => {
    const key = String(accountId);
    if (!pending.has(key)) {
      const next = Promise.resolve().then(() => request(accountId)).finally(() => { if (pending.get(key) === next) pending.delete(key); });
      pending.set(key, next);
    }
    return pending.get(key);
  };
  load.clear = () => pending.clear();
  return load;
}
