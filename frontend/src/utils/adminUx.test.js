import assert from "node:assert/strict";
import { test } from "node:test";
import { experienceDuration } from "./experienceDates.js";
import { courseImportExample, previewCourseImport } from "./courseImport.js";
import { addProfileSkill, skillKey, skillLevelFor, updateSkillLevel } from "./skillLevels.js";

test("employment duration uses years and months, including missing and partial dates", () => {
  for (const [months, expected] of [[45, "3 años y 9 meses"], [69, "5 años y 9 meses"], [12, "1 año"], [13, "1 año y 1 mes"], [1, "1 mes"], [11, "11 meses"], [24, "2 años"]]) assert.equal(experienceDuration(months), expected);
  for (const value of [undefined, null, "", 0, -1, 0.5, NaN, "Resumen profesional"]) assert.equal(experienceDuration(value), "Sin duración registrada");
});

test("course import previews the documented example as drafts without changing input", () => {
  const original = structuredClone(courseImportExample);
  const published = [{ ...original[0], active: true }];
  const preview = previewCourseImport(JSON.stringify(published));
  assert.equal(preview[0].active, false);
  assert.equal(published[0].active, true);
  assert.deepEqual(courseImportExample, original);
  assert.equal(preview[0].details.level, "beginner");
});

test("course import identifies invalid rows before saving", () => {
  assert.throws(() => previewCourseImport("[bad,"), /formato/);
  for (const rows of [{}, [], Array(51).fill(courseImportExample[0])]) assert.throws(() => previewCourseImport(JSON.stringify(rows)), /1 y 50/);
  for (const [field, value, message] of [["title", "", /nombre/], ["provider", "", /entidad/], ["skills", [], /habilidades/], ["hours", "12", /horas/], ["url", "http://example.com", /https/], ["category", "wrong", /área/], ["kind", "wrong", /tipo/], ["cost", "wrong", /coste/], ["details", { level: "expert" }, /nivel/]]) {
    assert.throws(() => previewCourseImport(JSON.stringify([{ ...courseImportExample[0], [field]: value }])), message);
  }
  assert.throws(() => previewCourseImport(JSON.stringify([courseImportExample[0], { ...courseImportExample[0], hours: 0 }])), /Curso 2/);
});

test("declared skill levels keep canonical aliases and remove unspecified levels", () => {
  assert.equal(skillKey("Administración"), "administracion");
  const levels = { python: "basic" };
  const changed = updateSkillLevel(levels, "JS", "advanced");
  assert.equal(skillLevelFor(changed, "JavaScript"), "advanced");
  assert.equal(skillLevelFor(changed, "SQL"), "unspecified");
  assert.deepEqual(levels, { python: "basic" });
  assert.deepEqual(updateSkillLevel(changed, "javascript", "unspecified"), levels);
});

test("adding a skill alias never duplicates or downgrades an existing declared level", () => {
  const profile = { skills: ["JavaScript"], skill_levels: { javascript: "expert" } };
  assert.equal(addProfileSkill(profile, "JS"), profile);
  const updated = addProfileSkill(profile, "SQL");
  assert.equal(updated.skill_levels.sql, "learning");
  assert.equal(updated.skill_levels.javascript, "expert");
  assert.deepEqual(profile.skills, ["JavaScript"]);
});
