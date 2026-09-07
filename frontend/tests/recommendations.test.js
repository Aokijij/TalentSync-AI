import assert from "node:assert/strict";
import test from "node:test";
import { selectRecommendations } from "../src/hooks/useRecommendations.js";

test("preserves recommendation metadata and does not mutate API records", () => {
  const record = Object.freeze({
    id: 1,
    match_percentage: 80,
    skill_match_percentage: 80,
    reasons: Object.freeze([
      "categoria:buenas",
      "score:skills:80",
      "Skills fuertes: python",
    ]),
  });
  const [selected] = selectRecommendations([record], 0, false);
  assert.equal(selected.category, "buenas");
  assert.equal(selected.strongSkills, true);
  assert.deepEqual(selected.reasons, ["Skills fuertes: python"]);
  assert.equal(record.reasons.length, 3);
});

test("keeps the original relevance thresholds and ordering", () => {
  const records = [
    { id: 1, match_percentage: 39.99, skill_match_percentage: 100 },
    { id: 2, match_percentage: 40, skill_match_percentage: 50 },
    { id: 3, match_percentage: 50, semantic_match_percentage: 75 },
    {
      id: 4,
      match_percentage: 60,
      skill_match_percentage: 30,
      semantic_match_percentage: 65,
    },
    {
      id: 5,
      match_percentage: 60,
      skill_match_percentage: 29.99,
      semantic_match_percentage: 65,
    },
  ];
  assert.deepEqual(
    selectRecommendations(records, 0, false).map(({ id }) => id),
    [2, 3, 4],
  );
  assert.deepEqual(
    selectRecommendations(records, 55, false).map(({ id }) => id),
    [4],
  );
});

test("uses legacy reason text when category tags are absent", () => {
  const record = {
    match_percentage: 80,
    semantic_match_percentage: 80,
    reasons: ["Alta similitud semántica"],
  };
  assert.equal(selectRecommendations([record], 0, false)[0].category, "alta");
  assert.deepEqual(selectRecommendations([record], 0, true), []);
  assert.deepEqual(selectRecommendations([], 0, false), []);
});
