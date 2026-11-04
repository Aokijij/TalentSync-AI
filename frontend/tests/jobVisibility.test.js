import assert from "node:assert/strict";
import test from "node:test";
import { isJobPublished } from "../src/utils/jobVisibility.js";

test("the full vacancy link requires actual publication", () => {
  assert.equal(isJobPublished({ status: "active", source_kind: "internal" }), true);
  assert.equal(isJobPublished({ status: "active", source_kind: "external", external_available: true }), true);
  for (const status of ["draft", "paused", "closed", "filled"]) assert.equal(isJobPublished({ status, external_available: true }), false);
  assert.equal(isJobPublished({ status: "active", source_kind: "external", external_available: false }), false);
  assert.equal(isJobPublished({ status: "active", source_kind: "external", external_available: true, moderation_status: "held" }), false);
  assert.equal(isJobPublished(null), false);
});
