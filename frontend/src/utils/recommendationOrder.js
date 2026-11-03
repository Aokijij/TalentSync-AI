export function orderRecommendations(items, mode) {
  return mode === "compatibility" ? [...items].sort((a, b) => b.match_percentage - a.match_percentage || a.job_id - b.job_id) : items;
}
