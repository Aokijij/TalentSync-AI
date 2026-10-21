import assert from "node:assert/strict";
import { test } from "node:test";
import { candidateOpportunities, companyOpportunities, processOverview, timestamp } from "../src/utils/dashboardData.js";

const now = Date.parse("2026-10-21T12:00:00Z");
test("dashboard queues exclude closed and released processes, and sort future interviews and recent applications", () => {
  const rows = [
    { id: 1, status: "submitted", response_due_at: "2026-10-20T12:00:00", created_at: "2026-10-19T10:00:00" },
    { id: 2, status: "reviewing", interview_at: "2026-10-22T10:00:00", created_at: "2026-10-21T10:00:00" },
    { id: 3, status: "technical_interview", interview_at: "2026-10-21T14:00:00Z" },
    { id: 4, status: "hired", interview_at: "2026-10-22T10:00:00", response_due_at: "2026-10-21T13:00:00Z" },
    { id: 5, status: "submitted", released_at: "2026-10-21T10:00:00", response_due_at: "2026-10-21T13:00:00Z" },
    { id: 6, status: "reviewing", interview_at: "2026-10-20T10:00:00" },
    { id: 7, status: "rejected", response_due_at: "2026-10-21T13:00:00Z" },
  ];
  const result = processOverview(rows, now);
  assert.deepEqual(result.active.map((row) => row.id), [1, 2, 3, 6]);
  assert.deepEqual(result.pending.map((row) => row.id), [1]);
  assert.deepEqual(result.urgent.map((row) => row.id), [1]);
  assert.deepEqual(result.interviews.map((row) => row.id), [3, 2]);
  assert.equal(result.recent[0].id, 2);
  assert.equal(result.selected, 1);
  assert.equal(timestamp("2026-10-21T12:00:00"), now);
  assert.equal(timestamp("2026-10-21T07:00:00-05:00"), now);
});

test("opportunities exclude expired, paused, unknown and already applied jobs", () => {
  const jobs = [{ id: 1, status: "active" }, { id: 2, status: "paused" }, { id: 3, status: "active", expires_at: "2026-10-20T12:00:00" }, { id: 4, status: "active" }, { id: 5, status: "active" }, { id: 6, status: "draft" }];
  const recommendations = [1, 2, 3, 4, 5, 99].map((id) => ({ job_id: id, match_percentage: id * 10 }));
  const applications = [{ job_id: 4, status: "rejected" }];
  assert.deepEqual(candidateOpportunities(recommendations, jobs, applications, now).map((row) => row.job_id), [5, 1]);
  const result = companyOpportunities(jobs, applications, now);
  assert.deepEqual(result.active.map((row) => row.id), [1, 4, 5]);
  assert.deepEqual(result.quiet.map((row) => row.id), [1, 5]);
  assert.equal(result.counts.get(4), 1);
  assert.deepEqual(result.drafts.map((row) => row.id), [6]);
});
