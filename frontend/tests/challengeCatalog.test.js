import assert from "node:assert/strict";
import { test } from "node:test";
import { filterChallenges } from "../src/utils/challengeCatalog.js";

test("challenge discovery combines skill, sector, level and result independently of courses", () => {
  const rows = [{ id: "basic", title: "Gestión de inventarios", skill: "inventarios", category: "logistics", level: "beginner", last_attempt: { passed: false, score: 0 } }, { id: "advanced", title: "Gestión de inventarios", category: "logistics", level: "advanced", last_attempt: { passed: true } }, { id: "excel", title: "Excel intermedio", category: "administration", level: "intermediate" }];
  assert.deepEqual(filterChallenges(rows, { query: "gestion", sector: "logistics", level: "beginner", status: "pending" }).map((row) => row.id), ["basic"]);
  assert.deepEqual(filterChallenges(rows, { status: "passed" }).map((row) => row.id), ["advanced"]);
  assert.deepEqual(filterChallenges(rows, { sector: "administration" }).map((row) => row.id), ["excel"]);
  assert.equal(filterChallenges(rows, { status: "active" }).length, 0);
  assert.equal(filterChallenges(rows, { query: "curso de inventarios" }).length, 0);
  assert.equal(filterChallenges([{ ...rows[0], state: { active: false }, last_attempt: { status: "active" } }], { status: "active" }).length, 0);
});
