import { useState } from "react";
import { comparisonIds, toggleComparedJob } from "../utils/jobComparison.js";

// JobsPage remounts on account changes. Only public IDs are kept in this tab.
export function useJobComparison(userId) {
  const key = `talentsync:compare:${userId}`;
  const [ids, setIds] = useState(() => {
    if (!userId) return [];
    try { return comparisonIds(window.sessionStorage.getItem(key)); } catch { return []; }
  });
  function update(next) {
    setIds(next);
    try { if (userId) window.sessionStorage.setItem(key, JSON.stringify(next)); } catch { /* Selection still works when storage is unavailable. */ }
  }
  return { ids, toggle: (id) => update(toggleComparedJob(ids, id)), clear: () => update([]) };
}
