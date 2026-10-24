import assert from "node:assert/strict";
import { test } from "node:test";
import { filterChallenges } from "../src/utils/challengeCatalog.js";

test("challenge filters combine skill text, level, result and course plan without losing zero scores", () => {
  const rows = [{ id: "basic", title: "Gestión de inventarios", skill: "inventarios", level: "beginner", last_attempt: { passed: false, score: 0 } }, { id: "advanced", title: "Gestión de inventarios", level: "advanced", last_attempt: { passed: true } }, { id: "excel", title: "Excel intermedio", level: "intermediate" }];
  assert.deepEqual(filterChallenges(rows, { query: "gestion", level: "beginner", status: "pending", onlyPlan: true }, new Set(["basic", "excel"])).map((row) => row.id), ["basic"]);
  assert.deepEqual(filterChallenges(rows, { status: "passed" }).map((row) => row.id), ["advanced"]);
  assert.equal(filterChallenges(rows, { status: "active" }).length, 0);
});
