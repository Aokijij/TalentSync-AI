import assert from "node:assert/strict";
import { test } from "node:test";
import { pendingCvMentions } from "./skillNames.js";
import { orderRecommendations } from "./recommendationOrder.js";
import { groupWritingHistory } from "./writingHistory.js";

test("the last confirmed mention disappears even when the saved skill has an accent", () => {
  const rows = [{ skill: "automatizacion", state: "project" }];
  assert.deepEqual(pendingCvMentions(rows, ["Automatización"], {}), []);
  assert.deepEqual(pendingCvMentions(rows, [], { automatizacion: "confirmed" }), []);
  assert.equal(pendingCvMentions(rows, [], {}).length, 1);
});
test("writing versions group by role, employer and employment period without combining rehires", () => {
  const record = { role: "Analista", company: "Empresa A", start_date: "2020-01" };
  const groups = groupWritingHistory([{ id: "old", record, created_at: "2026-10-10" }, { id: "new", record, created_at: "2026-10-14" }, { id: "rehire", record: { ...record, start_date: "2025-01" } }, { id: "other", record: { ...record, company: "Empresa B" } }]);
  assert.equal(groups.length, 3);
  assert.deepEqual(groups[0].rows.map((row) => row.id), ["new", "old"]);
});
test("highest compatibility sorts percentages strictly without a visibility override", () => {
  const rows = [{ job_id: 1, match_percentage: 61 }, { job_id: 2, match_percentage: 72, discovery: { visibility_reduced: true } }];
  assert.deepEqual(orderRecommendations(rows, "compatibility").map((row) => row.job_id), [2, 1]);
  assert.equal(orderRecommendations(rows, "balanced"), rows);
});
