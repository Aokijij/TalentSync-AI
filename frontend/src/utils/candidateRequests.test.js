import assert from "node:assert/strict";
import { test } from "node:test";
import { loadCandidatePages } from "./candidateRequests.js";

test("company pages publish intermediate results sequentially until every comparison is current", async () => {
  let active = 0, peak = 0;
  const pending = [20, 8, 0], seen = [];
  await loadCandidatePages({ request: async () => { active++; peak = Math.max(peak, active); await Promise.resolve(); active--; return { data: { pending: pending.shift(), items: [1] } }; }, onPage: (data) => seen.push(data.pending), wait: async () => {} });
  assert.deepEqual(seen, [20, 8, 0]); assert.equal(peak, 1);
});
test("a view change prevents publishing a late candidate response and stops polling", async () => {
  const controller = new AbortController(); let published = false, calls = 0;
  await loadCandidatePages({ signal: controller.signal, request: async () => { calls++; controller.abort(); return { data: { pending: 20 } }; }, onPage: () => { published = true; }, wait: async () => {} });
  assert.equal(published, false); assert.equal(calls, 1);
});
test("candidate polling backs off when another request is already scoring", async () => {
  let calls = 0; const delays = [];
  await loadCandidatePages({ request: async () => ({ data: { pending: ++calls === 5 ? 0 : 20 } }), onPage: () => {}, wait: async (delay) => delays.push(delay) });
  assert.deepEqual(delays, [500, 1000, 1500, 2000]);
});
