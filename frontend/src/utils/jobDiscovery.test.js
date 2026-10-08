import test from "node:test";
import assert from "node:assert/strict";
import { searchJob, visibleInterest, meetsRequiredPreferences } from "./jobDiscovery.js";
import { pageItems } from "./pagination.js";

test("required preferences filter known conflicts while retaining unknown conditions and the original score", () => {
  const records = [
    { job_id: 1, match_percentage: 95, match_details: { preferences: { unmet_conditions: ["Modalidad"], unknown_conditions: [] } } },
    { job_id: 2, match_percentage: 62, match_details: { preferences: { unmet_conditions: [], unknown_conditions: ["Salario mínimo"] } } },
    { job_id: 3, match_percentage: 80, match_details: { preferences: { unmet_conditions: [], unknown_conditions: [] } } },
  ];
  const before = structuredClone(records);
  assert.deepEqual(records.filter((row) => meetsRequiredPreferences(row)).map((row) => row.job_id), [2, 3]);
  assert.deepEqual(records.filter((row) => meetsRequiredPreferences(row, false)).map((row) => row.job_id), [1, 2, 3]);
  assert.deepEqual(records, before);
});

test("search and saved filters reach vacancies beyond the first 300 records", () => {
  const jobs = Array.from({ length: 350 }, (_, index) => ({ id: index + 1, title: index === 340 ? "Asesor de atención" : "Auxiliar", company_name: "Compañía Norte", location: "Bogotá", skills: ["Ventas"] }));
  const interests = new Map([[341, true], [350, false]]);
  const result = jobs.filter((job) => searchJob(job, "atencion bogota ventas") && visibleInterest(job, interests, "saved"));
  assert.deepEqual(pageItems(result, 1, 9).map((job) => job.id), [341]);
  assert.equal(jobs.filter((job) => visibleInterest(job, interests)).length, 349);
  assert.deepEqual(jobs.filter((job) => visibleInterest(job, interests, "hidden")).map((job) => job.id), [350]);
  interests.delete(350);
  assert.equal(jobs.filter((job) => visibleInterest(job, interests)).length, 350);
});
