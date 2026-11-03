import test from "node:test";
import assert from "node:assert/strict";
import { proposedResponseDate, responseState } from "../src/utils/responseDeadlines.js";

const now = new Date("2026-10-23T15:00:00Z");

test("overdue response retains an open candidature at the exact deadline", () => {
  assert.equal(responseState({ status: "reviewing", response_due_at: "2026-10-23T15:00:00" }, now), "overdue");
  assert.equal(responseState({ status: "reviewing", response_due_at: "2026-10-23T15:00:01" }, now), "on_time");
});

test("a pause and a selection outcome are independent states", () => {
  const row = { status: "reviewing", response_paused_at: "2026-10-23T14:00:00", response_due_at: "2026-10-20T15:00:00" };
  assert.equal(responseState(row, now), "paused");
  assert.equal(responseState({ ...row, status: "hired" }, now), "closed");
  assert.equal(responseState({ ...row, released_at: "2026-10-23T14:30:00" }, now), "closed");
});

test("a new commitment skips the Colombia weekend after an expired deadline", () => {
  assert.equal(proposedResponseDate("2026-10-20T15:00:00", now), "2026-10-26T15:00:00.000Z");
});

test("a new commitment extends the current promise when it is still in the future", () => {
  assert.equal(proposedResponseDate("2026-10-28T15:00:00", now), "2026-10-29T15:00:00.000Z");
});
