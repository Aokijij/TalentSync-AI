// Share only requests that are currently running; never retain account data.
export function createPendingLoader(request) {
  const pending = new Map();
  return (accountId) => {
    const key = String(accountId);
    if (!pending.has(key)) {
      const next = Promise.resolve().then(() => request(accountId)).finally(() => pending.delete(key));
      pending.set(key, next);
    }
    return pending.get(key);
  };
}
