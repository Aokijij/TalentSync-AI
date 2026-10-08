import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

export function useJobInterests(enabled = true, onChanged) {
  const [privacy, setPrivacy] = useState(null);
  const [signals, setSignals] = useState([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!enabled) return;
    let current = true;
    Promise.all([api.get("/account/privacy"), api.get("/personalization/feedback")]).then(([a, b]) => { if (current) { setPrivacy(a.data); setSignals(b.data); } }).catch((failure) => { if (current) setError(getApiErrorMessage(failure)); });
    return () => { current = false; };
  }, [enabled]);
  async function act(action) {
    setBusy(true); setError(""); setNotice("");
    try { await action(); setNotice("Interés actualizado"); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  function save(jobId, interested) {
    return act(async () => {
      await api.put("/personalization/feedback", { job_id: jobId, interested });
      setSignals((rows) => [...rows.filter((row) => row.job_id !== jobId), { job_id: jobId, interested }]);
      await onChanged?.();
    });
  }
  function remove(jobId) {
    return act(async () => { await api.delete(`/personalization/feedback/${jobId}`); setSignals((rows) => rows.filter((row) => row.job_id !== jobId)); await onChanged?.(); });
  }
  function consent(value) {
    return act(async () => { const { data } = await api.put("/account/privacy", { ...privacy, personalize_recommendations: value }); setPrivacy(data); if (!value) setSignals([]); await onChanged?.(); });
  }
  const byId = new Map(signals.map((row) => [row.job_id, row.interested]));
  return { privacy, signals, byId, busy, notice, error, save, remove, consent, enabled: !!privacy?.personalize_recommendations };
}
