import assert from "node:assert/strict";
import { test } from "node:test";
import { welcomePreferences, welcomeChanges, companyWelcomeState } from "../src/utils/welcome.js";

test("welcome preserves saved preferences and produces no write for unchanged values", () => {
  const values = welcomePreferences({ profession: "Analista", location: "Medellín", preferred_modality: "onsite", desired_salary: 2500000 });
  assert.equal(values.modality, "onsite");
  assert.deepEqual(welcomeChanges(values, { ...values }), {});
  assert.deepEqual(welcomePreferences(), { profession: "", city: "", modality: "", salary: "", sector: "", availability: "" });
});
test("welcome changes only edited fields, normalizes city and clears department on removing location", () => {
  const initial = welcomePreferences({ profession: "Analista", location: "Bogotá", preferred_modality: "hybrid", desired_salary: 2500000 });
  assert.deepEqual(welcomeChanges(initial, { ...initial, profession: "  Contador  " }), { profession: "Contador" });
  assert.deepEqual(welcomeChanges(initial, { ...initial, city: "medellin" }), { location: "Medellín", department: "Antioquia" });
  assert.deepEqual(welcomeChanges(initial, { ...initial, city: "" }), { location: null, department: null });
  assert.deepEqual(welcomeChanges(initial, { ...initial, salary: "" }), { desired_salary: null });
  assert.throws(() => welcomeChanges(initial, { ...initial, city: "Ciudad inexistente" }), /catálogo/);
  for (const salary of ["0", "-1", "Infinity", "1000000001"]) assert.throws(() => welcomeChanges(initial, { ...initial, salary }), /aspiración/);
});
test("company welcome distinguishes review from approval and respects security requirements", () => {
  const org = { role: "owner", verification_required: true, verification_status: "reviewing", submission: { submitted_at: "2026-10-23" } };
  const user = { email_verified: true, mfa_enabled: true };
  assert.equal(companyWelcomeState(org, user).submitted, true);
  assert.equal(companyWelcomeState(org, user).ready, false);
  assert.equal(companyWelcomeState({ ...org, verification_status: "verified" }, user).ready, true);
  assert.equal(companyWelcomeState({ ...org, verification_status: "verified" }, { ...user, email_verified: false }).ready, false);
  assert.equal(companyWelcomeState({ ...org, verification_status: "verified" }, { ...user, mfa_enabled: false }).ready, false);
  assert.equal(companyWelcomeState({ ...org, verification_status: "suspended", verification_required: false }, user).ready, false);
  const exempt = companyWelcomeState({ ...org, verification_status: "pending", verification_required: false }, user);
  assert.equal(exempt.ready, true);
  assert.match(exempt.reviewText, /no equivale/);
  assert.equal(companyWelcomeState({ ...org, verification_status: "unexpected" }, user).ready, false);
});
