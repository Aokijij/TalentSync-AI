import assert from "node:assert/strict";
import { test } from "node:test";
import { createPendingLoader } from "./pendingRequests.js";

test("simultaneous requests share work only within the same account and release completed data", async () => {
  let calls = 0;
  const resolvers = [];
  const load = createPendingLoader((accountId) => { calls++; return new Promise((resolve) => resolvers.push(() => resolve({ accountId }))); });
  const first = load(1), duplicate = load(1), other = load(2);
  assert.equal(first, duplicate);
  assert.notEqual(first, other);
  await Promise.resolve();
  assert.equal(calls, 2);
  resolvers.splice(0).forEach((resolve) => resolve());
  assert.deepEqual(await first, { accountId: 1 });
  assert.deepEqual(await other, { accountId: 2 });
  const fresh = load(1);
  assert.notEqual(first, fresh);
  await Promise.resolve();
  assert.equal(calls, 3);
  resolvers[0]();
  await fresh;
});

test("failed requests are released so a manual retry can run", async () => {
  let calls = 0;
  const load = createPendingLoader(() => { calls++; throw new Error("Unavailable"); });
  await assert.rejects(load(1));
  await assert.rejects(load(1));
  assert.equal(calls, 2);
});
