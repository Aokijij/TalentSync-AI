import assert from "node:assert/strict";
import { test } from "node:test";
import { credentialStatus } from "../src/constants/credentials.js";
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

test("expiry display uses the selected date and resume draft retains credential fields", () => {
  assert.equal(credentialStatus({ status: "valid", expires_on: "2026-10-16" }, "2026-10-16"), "Vigente");
  assert.equal(credentialStatus({ status: "valid", expires_on: "2026-10-15" }, "2026-10-16"), "Vencida por fecha");
  const profile = { driving_licenses: [{ category: "B1" }], professional_cards: [{ profession: "Arquitectura" }] };
  const payload = resumeExportPayload(profile, "Persona", { sections: ["certifications"], includePhoto: false, style: "minimal", color: "default" });
  assert.deepEqual(payload.profile.driving_licenses, profile.driving_licenses);
  assert.deepEqual(payload.profile.professional_cards, profile.professional_cards);
});
