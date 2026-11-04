import assert from "node:assert/strict";
import test from "node:test";
import { remoteScopeFromLegacy } from "../src/utils/remoteScope.js";
import { externalJobFields, externalJobChanges } from "../src/utils/externalJobEditor.js";

test("an incomplete imported offer has no implicit changes when opened", () => {
  const before = externalJobFields({ id: 1, description: "Parcial", requirements: "", skills: ["sql"] });
  assert.deepEqual(externalJobChanges(before, structuredClone(before)), {});
});
test("partial changes preserve missing fields and distinguish no experience from unknown", () => {
  const before = externalJobFields({ quality_details: { experience_months: 12, contract_type: "indefinite" }, languages: [{ name: "inglés", level: "B1" }] });
  const after = structuredClone(before);
  after.quality_details.experience_months = 0;
  after.languages = [];
  assert.deepEqual(externalJobChanges(before, after), { languages: [], quality_details: { experience_months: 0 } });
  after.quality_details.experience_months = null;
  assert.equal(externalJobChanges(before, after).quality_details.experience_months, null);
  assert.equal(before.quality_details.experience_months, 12);
});

test("missing imported location opens the remote scope without crashing", () => {
  assert.deepEqual(remoteScopeFromLegacy(null), { mode: "global", countries: [], continents: [] });
});
