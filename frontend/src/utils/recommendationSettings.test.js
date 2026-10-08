import assert from "node:assert/strict";
import test from "node:test";
import { readRecommendationSettings, saveRecommendationSetting } from "./recommendationSettings.js";

test("recommendation filters belong to each account and retain zero in both views", () => {
  const values = new Map([["talentsync_recommendation_min", "90"]]);
  const storage = { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) };
  assert.deepEqual(readRecommendationSettings(storage, 1), { minimum: 40, source: "all" });
  saveRecommendationSetting(storage, 1, "minimum", 0);
  saveRecommendationSetting(storage, 1, "source", "external");
  assert.deepEqual(readRecommendationSettings(storage, 1), { minimum: 0, source: "external" });
  assert.deepEqual(readRecommendationSettings(storage, 2), { minimum: 40, source: "all" });
  saveRecommendationSetting(storage, 2, "minimum", 70);
  assert.equal(readRecommendationSettings(storage, 2).minimum, 70);
  assert.equal(readRecommendationSettings(storage, 1).minimum, 0);
});

test("invalid, missing and unavailable browser settings use usable defaults", () => {
  const storage = { getItem: () => "unexpected" };
  assert.deepEqual(readRecommendationSettings(storage, 1), { minimum: 40, source: "all" });
  assert.deepEqual(readRecommendationSettings({ getItem() { throw new Error("unavailable"); } }, 1), { minimum: 40, source: "all" });
  assert.deepEqual(readRecommendationSettings(storage, null), { minimum: 40, source: "all" });
});
