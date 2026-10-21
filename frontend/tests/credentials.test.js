import assert from "node:assert/strict";
import { test } from "node:test";
import { offerDraft, offerPayload } from "../src/utils/offerQuality.js";
import { resumeExportPayload } from "../src/utils/resumeExport.js";

test("document requirements survive offer editing without leaking into other drafts", () => {
  const original = { quality_details: { credential_requirements: { driving_categories: ["B1"], professional_cards: ["Ingeniería civil"] } } };
  const draft = offerDraft(original);
  draft.quality_details.credential_requirements.driving_categories.push("C1");
  assert.deepEqual(original.quality_details.credential_requirements.driving_categories, ["B1"]);
  assert.deepEqual(offerPayload(draft).quality_details.credential_requirements, { driving_categories: ["B1", "C1"], professional_cards: ["Ingeniería civil"] });
  assert.deepEqual(offerDraft().quality_details.credential_requirements, { driving_categories: [], professional_cards: [] });
});

test("resume draft retains independent credential fields", () => {
  const profile = { driving_licenses: [{ category: "B1" }], professional_cards: [{ profession: "Arquitectura" }] };
  const payload = resumeExportPayload(profile, "Persona", { sections: ["certifications"], includePhoto: false, style: "minimal", color: "default" });
  assert.deepEqual(payload.profile.driving_licenses, profile.driving_licenses);
  assert.deepEqual(payload.profile.professional_cards, profile.professional_cards);
});
