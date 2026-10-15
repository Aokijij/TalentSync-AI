import { api } from "./client.js";
import { createProgressiveLoader } from "../utils/progressiveRequests.js";

const feed = createProgressiveLoader(() => api.get("/recommendations/me/jobs/batch", {
  params: { batch_size: 12 }, timeout: 20000, __skipRetry: true,
}));
export const getRecommendations = feed.load;
export const subscribeRecommendations = feed.subscribe;
window.addEventListener("talentsync:requests-canceled", feed.cancel);
