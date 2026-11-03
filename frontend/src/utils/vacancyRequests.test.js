import assert from "node:assert/strict";
import { test } from "node:test";
import { loadVacancyData } from "./vacancyRequests.js";

test("slow responses from a previous similar vacancy cannot replace the new vacancy or match", async () => {
  const calls = [];
  const request = (url, options) => new Promise((resolve) => calls.push({ url, signal: options.signal, resolve }));
  const client = { get: request, post: (url, body, options) => request(url, options) };
  const seen = [];
  const handlers = { job: (value) => seen.push(["job", value.id]), match: (value) => seen.push(["match", value.id]), catalog: () => {}, applications: () => {}, company: () => {}, error: () => assert.fail("Unexpected error") };
  const cancelA = loadVacancyData(client, { jobId: 1, role: "candidate" }, handlers);
  cancelA();
  const cancelB = loadVacancyData(client, { jobId: 2, role: "candidate" }, handlers);
  for (const call of calls.slice(4)) call.resolve({ data: { id: 2 } });
  await Promise.resolve();
  for (const call of calls.slice(0, 4)) call.resolve({ data: { id: 1 } });
  await Promise.resolve();
  assert.deepEqual(seen, [["job", 2], ["match", 2]]);
  assert.ok(calls.slice(0, 4).every((call) => call.signal.aborted));
  cancelB();
});

test("cancelled match calculations are quiet while genuine failures use the inline handler", async () => {
  for (const cancelled of [true, false]) {
    let failures = 0;
    const client = { get: async () => ({ data: [] }), post: async (url, body, options) => { assert.equal(options.__quiet, true); throw Object.assign(new Error("failed"), { code: cancelled ? "ERR_CANCELED" : "ERR_NETWORK" }); } };
    const stop = loadVacancyData(client, { jobId: 3, role: "candidate" }, { job() {}, catalog() {}, applications() {}, match() {}, matchError() { failures++; }, error() { assert.fail("Not a vacancy load error"); } });
    await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
    assert.equal(failures, cancelled ? 0 : 1);
    stop();
  }
});
