const defaults = { minimum: 40, source: "all" };
const allowed = { minimum: [0, 40, 50, 60, 70, 80, 90], source: ["all", "internal", "external"] };
const key = (userId, setting) => `talentsync_recommendations:${userId}:${setting}`;

export function readRecommendationSettings(storage, userId) {
  const result = { ...defaults };
  if (!userId) return result;
  try {
    for (const setting of Object.keys(defaults)) {
      const raw = storage.getItem(key(userId, setting));
      const value = setting === "minimum" ? Number(raw) : raw;
      if (raw !== null && raw !== "" && allowed[setting].includes(value)) result[setting] = value;
    }
  } catch { /* Browsing without persistent storage keeps the defaults. */ }
  return result;
}

export function saveRecommendationSetting(storage, userId, setting, value) {
  if (!userId || !allowed[setting]?.includes(value)) return;
  try { storage.setItem(key(userId, setting), String(value)); } catch { /* The current view still uses its in-memory selection. */ }
}
