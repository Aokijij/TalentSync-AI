import test from "node:test";
import assert from "node:assert/strict";
import { searchJob, visibleInterest } from "./jobDiscovery.js";
import { pageItems } from "./pagination.js";

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
