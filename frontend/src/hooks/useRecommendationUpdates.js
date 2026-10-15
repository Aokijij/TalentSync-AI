import { useEffect, useState } from "react";
import { subscribeRecommendations } from "../api/recommendations.js";

export function useRecommendationUpdates(accountId, setRecommendations) {
  const [refreshing, setRefreshing] = useState(false);
  useEffect(() => {
    if (accountId == null) return;
    return subscribeRecommendations(accountId, (items, pending) => {
      if (items) setRecommendations(items);
      setRefreshing(pending);
    });
  }, [accountId, setRecommendations]);
  return refreshing;
}
