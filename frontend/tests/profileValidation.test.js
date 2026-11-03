import assert from "node:assert/strict";
import { test } from "node:test";
import { profileServerErrors, profileValidation, focusProfileError } from "../src/utils/profileValidation.js";
import { academicPresentation } from "../src/utils/academicPresentation.js";

test("profile errors identify the specific row and field, including duplicates and private birth dates", () => {
  const result = profileValidation({ links: [{ platform: "github", url: "github.com/a" }, { platform: "linkedin", url: "example.com" }], birth_date: "2099-01-01", driving_licenses: [{ category: "A2" }, { category: "A2" }], professional_cards: [{ profession: "" }], certifications: [{ year: "2099", url: "http://example.com" }] }, "Ana", "2026-10-21");
  assert.deepEqual(Object.keys(result), ["links.1.url", "birth_date", "driving_licenses.1.category", "professional_cards.0.profession", "certifications.0.year", "certifications.0.url"]);
  assert.deepEqual(profileValidation({ birth_date: null }, "Ana", "2026-10-21"), {});
  const server = profileServerErrors({ response: { data: { detail: [{ loc: ["body", "links", 2], type: "value_error", msg: "Value error, El enlace debe pertenecer a github.com" }] } } });
  assert.match(server["links.2.url"], /github.com/);
});

test("focus goes directly to the invalid field without sending the user to the page top", () => {
  let focused = false, scrolled = false;
  const target = { dataset: { fieldPath: "links.2.url" }, scrollIntoView(options) { scrolled = options.block === "center"; }, querySelector() { return { focus() { focused = true; } }; } };
  focusProfileError({ "links.2.url": "Enlace inválido" }, { querySelectorAll() { return [target]; } });
  assert.equal(focused && scrolled, true);
});

const academic = { status: "partial", requested_fields: ["Ingeniería de Sistemas"], required_level: "university", accepts_in_progress: false, selected: { status: "exact", actual_level: "university", candidate_degree: "Ingeniería de Sistemas", requested_field: "Ingeniería de Sistemas", in_progress: true } };
test("academic explanations distinguish matching area and level from unfinished studies", () => {
  const result = academicPresentation(academic);
  assert.deepEqual(result.checks.map((row) => row.tone), ["met", "met", "unmet"]);
  assert.match(result.title, /falta finalizarla/);
  const students = academicPresentation({ ...academic, accepts_in_progress: true });
  assert.ok(students.checks.every((row) => row.tone === "met"));
  const finished = academicPresentation({ ...academic, selected: { ...academic.selected, in_progress: false } });
  assert.equal(finished.tone, "fulfilled");
  assert.ok(!finished.summary.includes("parcial"));
  const related = academicPresentation({ ...academic, selected: { ...academic.selected, status: "related", in_progress: false } });
  assert.equal(related.checks[0].tone, "partial");
  const unknown = academicPresentation({ ...academic, selected: { ...academic.selected, status: "review", actual_level: null } });
  assert.deepEqual(unknown.checks.map((row) => row.tone), ["review", "review", "unmet"]);
});
