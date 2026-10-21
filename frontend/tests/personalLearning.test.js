import assert from "node:assert/strict";
import { test } from "node:test";
import { requiresAuthenticator } from "../src/utils/accountAccess.js";
import { personalDetailLines } from "../src/utils/personalDetails.js";
import { resumeExportPayload } from "../src/utils/resumeExport.js";
import { challengeState } from "../src/utils/learningChallenges.js";

test("local MFA pause overrides setup flags while production still requires the configured authenticator", () => {
  const user = { role: "company", mfa_enabled: false };
  assert.equal(requiresAuthenticator(user, { mode: "session", company_mfa_required: true }), true);
  assert.equal(requiresAuthenticator(user, { mode: "session", company_mfa_required: true, mfa_review: true }), false);
  assert.equal(requiresAuthenticator(user, { mode: "session", company_mfa_required: false }), false);
  assert.equal(requiresAuthenticator(user, { mode: "session" }), false);
  assert.equal(requiresAuthenticator({ role: "admin" }, { mode: "session", admin_mfa_required: true }), true);
});

test("each personal detail has an independent visibility choice and the PDF draft carries the current choices", () => {
  const profile = { birth_date: "1999-12-13", identification: { type: "CC", number: "EXAMPLE-1234" }, personal_visibility: { birth_date: false, identification: true } };
  assert.deepEqual(personalDetailLines(profile), [["Cédula de ciudadanía", "EXAMPLE-1234"]]);
  assert.deepEqual(personalDetailLines({ ...profile, personal_visibility: {} }), []);
  assert.deepEqual(personalDetailLines({ ...profile, identification: null }, true), [["Nacimiento", "13/12/1999"]]);
  const payload = resumeExportPayload(profile, "Ejemplo", { sections: ["contact"], style: "modern", color: "default", includePhoto: false });
  assert.deepEqual(payload.profile.personal_visibility, profile.personal_visibility);
  assert.deepEqual(payload.profile.identification, profile.identification);
});

test("challenge continuation and retry cooldown use server UTC times without blocking result review", () => {
  const now = Date.parse("2026-10-21T12:00:00Z");
  const row = { last_attempt: { status: "active", started_at: "2026-10-21T11:55:00", expires_at: "2026-10-21T12:05:00" } };
  assert.equal(challengeState(row, now).active, true);
  assert.equal(challengeState(row, now).waiting, false);
  const completed = challengeState({ last_attempt: { ...row.last_attempt, status: "completed", passed: false, score: 40 } }, now);
  assert.equal(completed.waiting && completed.completed, true);
  assert.equal(completed.retryAt, Date.parse("2026-10-22T11:55:00Z"));
  assert.equal(challengeState(row, now + 86400000).waiting, false);
  assert.equal(challengeState({}, now).label, "Empezar práctica");
});
