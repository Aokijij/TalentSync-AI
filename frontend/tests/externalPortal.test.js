import assert from "node:assert/strict";
import test from "node:test";

import {
  cleanExternalLocation,
  externalPortal,
} from "../src/utils/externalPortal.js";

test("shows the destination portal without exposing the technical provider", () => {
  const job = {
    external_url: "https://co.linkedin.com/jobs/view/123",
    location: "Bogotá • a través de LinkedIn",
  };

  assert.equal(externalPortal(job), "LinkedIn");
  assert.equal(cleanExternalLocation(job.location), "Bogotá");
});

test("keeps a useful neutral destination when the employer site is unknown", () => {
  assert.equal(externalPortal({ external_url: "https://careers.example.com/job/1" }), "el sitio de la empresa");
});
