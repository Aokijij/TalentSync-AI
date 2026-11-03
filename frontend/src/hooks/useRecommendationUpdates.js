import { useEffect, useState } from "react";
import { getRecommendations, subscribeRecommendations } from "../api/recommendations.js";

export function useRecommendationUpdates(accountId, setRecommendations) {
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (accountId == null) return;
    return subscribeRecommendations(accountId, (items, pending, failure) => {
      if (items) setRecommendations(items);
      setRefreshing(pending);
      setError(failure ? "No pudimos terminar de actualizar las compatibilidades. Tus resultados cargados siguen disponibles." : "");
    });
  }, [accountId, setRecommendations]);
  async function retry() {
    setError(""); setRefreshing(true);
    try { await getRecommendations(accountId); }
    catch { setRefreshing(false); setError("No pudimos actualizar las compatibilidades. Vuelve a intentarlo."); }
  }
  return { refreshing, error, retry };
}
