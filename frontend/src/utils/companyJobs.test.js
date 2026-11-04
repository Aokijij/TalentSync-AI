import assert from "node:assert/strict";
import { test } from "node:test";
import { companyJobCounts, filterCompanyJobs } from "./companyJobs.js";

const jobs = [
  { id: 1, title: "Analista de datos", status: "draft", skills: ["comunicacion"], quality_summary: { can_publish: true } },
  { id: 2, title: "Diseño de producto", status: "draft", skills: ["figma"], quality_summary: { can_publish: false } },
  { id: 3, title: "Desarrollo de APIs", status: "active", skills: ["python"], quality_summary: { can_publish: true } },
  { id: 4, title: "Soporte", status: "closed", quality_summary: { can_publish: true } },
];
test("readiness counts include drafts only and never present closed vacancies as paused", () => {
  assert.deepEqual(companyJobCounts(jobs), { total: 4, active: 1, draft: 2, paused: 0, ready: 1, incomplete: 1 });
  assert.deepEqual(filterCompanyJobs(jobs, { status: "closed" }).map(job => job.id), [4]);
});
test("company filters combine status, readiness and accent-insensitive skills", () => {
  assert.deepEqual(filterCompanyJobs(jobs, { query: "comunicación", status: "draft", readiness: "ready" }).map(job => job.id), [1]);
  assert.deepEqual(filterCompanyJobs(jobs, { query: "diseno", readiness: "incomplete" }).map(job => job.id), [2]);
  assert.equal(filterCompanyJobs(jobs, { query: "python", status: "draft" }).length, 0);
});
