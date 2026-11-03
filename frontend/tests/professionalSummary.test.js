import test from "node:test";
import assert from "node:assert/strict";
import { summaryInput, withCustomSummary } from "../src/utils/professionalSummary.js";

test("local AI receives professional facts from the draft without contact data", () => {
  const profile = { profession: "Analista", email: "private@example.com", phone: "3001234567", skills: ["SQL"], experience: "Mi resumen", experiences: [{ role: "Analista", description: "Revisé informes", company: "Empresa privada", end_year: "Presente" }], educations: [{ degree: "Tecnología", institution: "Institución privada", end_year: "En curso" }] };
  const facts = summaryInput(profile);
  assert.equal(facts.experiences[0].is_current, true);
  assert.equal(facts.educations[0].is_current, true);
  assert.equal(facts.experience, "Mi resumen");
  const text = JSON.stringify(facts);
  for (const privateData of [profile.email, profile.phone, "Empresa privada", "Institución privada"]) assert.ok(!text.includes(privateData));
  assert.deepEqual(summaryInput({}).skills, []);
});

test("personal text and accepted proposals explicitly opt out of automatic regeneration", () => {
  const profile = { experience: "Resumen anterior", summary_mode: "automatic", skills: ["SQL"], phone: "3001234567" };
  const draft = withCustomSummary(profile, "Mi propio texto");
  assert.equal(draft.summary_mode, "custom");
  assert.equal(draft.experience, "Mi propio texto");
  assert.deepEqual(draft.skills, profile.skills);
  assert.equal(draft.phone, profile.phone);
  assert.equal(profile.experience, "Resumen anterior");
});
