import assert from "node:assert/strict";
import { test } from "node:test";
import { createProgressiveLoader } from "./progressiveRequests.js";

const tick = () => new Promise((resolve) => setImmediate(resolve));

test("a transient background failure retries and eventually publishes completed data", async () => {
  let calls = 0;
  const pauses = [], updates = [];
  const feed = createProgressiveLoader(async () => {
    if (++calls === 2) throw new Error("Temporary network failure");
    return { data: { items: [calls], pending: calls < 3 ? 1 : 0 } };
  }, () => new Promise((resolve) => pauses.push(resolve)));
  const leave = feed.subscribe(1, (items, pending, failure) => updates.push({ items, pending, failure }));
  await feed.load(1);
  pauses.shift()(); await tick();
  pauses.shift()(); await tick();
  assert.equal(calls, 3);
  assert.deepEqual(updates.at(-1).items, [3]);
  assert.equal(updates.at(-1).pending, false);
  assert.equal(updates.at(-1).failure, null);
  leave();
});

test("the first batch renders before the remaining work and overlapping views share requests", async () => {
  let calls = 0;
  const pauses = [];
  const updates = [];
  const feed = createProgressiveLoader(async () => {
    calls++;
    return { data: { items: Array.from({ length: calls }, (_, i) => ({ job_id: i + 1 })), pending: calls === 1 ? 1 : 0 } };
  }, () => new Promise((resolve) => pauses.push(resolve)));
  const unsubscribe = feed.subscribe(1, (items, pending) => updates.push({ items, pending }));
  const [first, duplicate] = await Promise.all([feed.load(1), feed.load(1)]);
  assert.equal(calls, 1);
  assert.equal(first.data.length, 1);
  assert.deepEqual(first.data, duplicate.data);
  assert.equal(updates.at(-1).pending, true);
  pauses[0]();
  await tick();
  assert.equal(calls, 2);
  assert.equal(updates.at(-1).items.length, 2);
  assert.equal(updates.at(-1).pending, false);
  unsubscribe();
});

test("leaving a screen stops its polling without interrupting another account", async () => {
  const calls = [];
  const pauses = [];
  const updates = [];
  const feed = createProgressiveLoader(async (id) => {
    calls.push(id);
    return { data: { items: [{ account: id }], pending: calls.filter((value) => value === id).length === 1 ? 1 : 0 } };
  }, () => new Promise((resolve) => pauses.push(resolve)));
  const leave = feed.subscribe(1, () => {});
  const leaveOther = feed.subscribe(2, (items) => updates.push(items));
  await Promise.all([feed.load(1), feed.load(2)]);
  leave();
  pauses.splice(0).forEach((resolve) => resolve());
  await tick();
  assert.deepEqual(calls, [1, 2, 2]);
  assert.deepEqual(updates.at(-1), [{ account: 2 }]);
  leaveOther();
});

test("logout rejects late account data and a fresh login can start immediately", async () => {
  const resolvers = [];
  const updates = [];
  const feed = createProgressiveLoader(() => new Promise((resolve) => resolvers.push(resolve)));
  const leave = feed.subscribe(1, (items) => updates.push(items));
  const old = feed.load(1);
  const rejected = assert.rejects(old, { code: "ERR_CANCELED" });
  await tick();
  feed.cancel();
  const fresh = feed.load(1);
  await tick();
  assert.equal(resolvers.length, 2);
  resolvers[0]({ data: { items: [{ private: "old" }], pending: 0 } });
  await rejected;
  resolvers[1]({ data: { items: [{ private: "fresh" }], pending: 0 } });
  assert.deepEqual((await fresh).data, [{ private: "fresh" }]);
  assert.deepEqual(updates, [[{ private: "fresh" }]]);
  leave();
});
