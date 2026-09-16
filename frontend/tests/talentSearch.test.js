import assert from "node:assert/strict";
import test from "node:test";
import { matchingSkills, searchTalent } from "../src/utils/talentSearch.js";

const candidates = Object.freeze([
  Object.freeze({ user_id: 1, name: "Valentina Gómez", profession: "Analista", skills: ["SQL"], has_applied: true, match_percentage: 88 }),
  Object.freeze({ user_id: 2, name: "Santiago Ramírez", profession: "Analista financiero", skills: ["SQL", "Python"], has_applied: false, match_percentage: 80 }),
  Object.freeze({ user_id: 3, name: "Andrea", skills: null, has_applied: false, match_percentage: 70 }),
]);

test("separates people to invite from existing applications without mutating results", () => {
  assert.deepEqual(searchTalent(candidates).map((item) => item.user_id), [2, 3]);
  assert.deepEqual(searchTalent(candidates, { audience: "applied" }).map((item) => item.user_id), [1]);
  assert.deepEqual(searchTalent(candidates, { minMatch: 80 }).map((item) => item.user_id), [2]);
});

test("search supports accents, profession, skills and multiple search words", () => {
  assert.equal(searchTalent(candidates, { query: "ramirez python" })[0].user_id, 2);
  assert.equal(searchTalent(candidates, { query: "GOMEZ", audience: "applied" })[0].user_id, 1);
  assert.deepEqual(searchTalent(candidates, { query: "diseñador" }), []);
});

test("shows only skills required by the selected vacancy", () => {
  assert.deepEqual(matchingSkills(["ANALISIS financiero", "python"], ["análisis financiero", "SQL"]), ["análisis financiero"]);
  assert.deepEqual(matchingSkills(null, null), []);
});

test("the default minimum includes exactly 50 percent and excludes lower scores", () => {
  const records = [49.99, 50, 59].map((score) => ({ name: "Candidato", match_percentage: score, has_applied: false }));
  assert.deepEqual(searchTalent(records).map((item) => item.match_percentage), [59, 50]);
});
