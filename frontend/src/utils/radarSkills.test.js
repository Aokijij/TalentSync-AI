import assert from "node:assert/strict";
import { test } from "node:test";
import { browseRadarSkills } from "./radarSkills.js";

test("all skills use demand order and bounded pages, including zero-demand skills", () => {
  const rows = Array.from({ length: 46 }, (_, i) => ({ skill: `habilidad ${i}`, count: i }));
  const first = browseRadarSkills(rows);
  assert.equal(first.rows.length, 5);
  assert.equal(first.rows[0].count, 45);
  assert.equal(first.pages, 10);
  const last = browseRadarSkills(rows, "", 100);
  assert.equal(last.page, 10);
  assert.equal(last.rows.length, 1);
  assert.equal(last.rows[0].count, 0);
  assert.equal(rows[0].count, 0);
});

test("skill search ignores accents and handles an empty result", () => {
  const rows = [{ skill: "administración", count: 2 }, { skill: "python", count: 10 }];
  assert.equal(browseRadarSkills(rows, "ADMINISTRACION").rows[0].skill, "administración");
  assert.deepEqual(browseRadarSkills(rows, "none").rows, []);
});
