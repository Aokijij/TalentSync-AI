import { api } from "./client.js";
import { createPendingLoader } from "../utils/pendingRequests.js";

export const getRecommendations = createPendingLoader(() => api.get("/recommendations/me/jobs", {
  params: { include_all: true }, timeout: 45000, __skipRetry: true,
}));
