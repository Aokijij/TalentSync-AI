import assert from "node:assert/strict";
import test from "node:test";
import { matchingSkills, talentInvitation } from "../src/utils/talentSearch.js";

test("talent cards and comparison show only declared skills required by the selected vacancy", () => {
  assert.deepEqual(matchingSkills(["ANALISIS financiero", "python"], ["análisis financiero", "SQL"]), ["análisis financiero"]);
  assert.deepEqual(matchingSkills(null, null), []);
});

test("invitation eligibility follows the server's professional threshold rather than the obsolete sixty-percent UI limit", () => {
  assert.equal(talentInvitation({ professional_match_percentage: 50, match_percentage: 45 }).allowed, true);
  assert.equal(talentInvitation({ professional_match_percentage: 49.99, match_percentage: 70 }).allowed, false);
  assert.match(talentInvitation({ match_percentage: 40 }).reason, /50%/);
});

test("invitations explain known conflicts, existing applications and pending invitations", () => {
  const candidate = { professional_match_percentage: 80, match_percentage: 70 };
  for (const changes of [{ has_applied: true }, { has_pending_invitation: true }, { location_fit: { invitation_allowed: false } }]) {
    const result = talentInvitation({ ...candidate, ...changes });
    assert.equal(result.allowed, false);
    assert.ok(result.reason.length > 10);
  }
  assert.equal(talentInvitation({}).allowed, false);
});
