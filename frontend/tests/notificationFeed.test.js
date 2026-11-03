import assert from "node:assert/strict";
import test from "node:test";
import { createNotificationFeed } from "../src/utils/notificationFeed.js";

function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }

test("switching notification filters cancels the old request and ignores late data", async () => {
  const calls = [], states = [];
  const feed = createNotificationFeed((params, signal) => { const pending = deferred(); calls.push({ params, signal, ...pending }); return pending.promise; }, (state) => states.push(state), 2);
  const old = feed.reset("all");
  const current = feed.reset("unread");
  assert.equal(calls[0].signal.aborted, true);
  assert.equal(calls[1].params.unread_only, true);
  calls[1].resolve([{ id: 7, is_read: false }]); await current;
  calls[0].resolve([{ id: 1, is_read: true }]); await old;
  assert.deepEqual(states.at(-1).items.map((row) => row.id), [7]);
  assert.equal(states.at(-1).loading, false);
});

test("overlapping pages are deduplicated without losing the server cursor and double clicks share a single load", async () => {
  const calls = [], states = [];
  const feed = createNotificationFeed((params) => { const pending = deferred(); calls.push({ params, ...pending }); return pending.promise; }, (state) => states.push(state), 2);
  let running = feed.reset("applications"); calls[0].resolve([{ id: 5 }, { id: 4 }]); await running;
  running = feed.more(); await feed.more();
  assert.equal(calls.length, 2);
  assert.equal(calls[1].params.category, "applications");
  assert.equal(calls[1].params.offset, 2);
  calls[1].resolve([{ id: 4 }, { id: 3 }]); await running;
  assert.deepEqual(states.at(-1).items.map((row) => row.id), [5, 4, 3]);
  running = feed.more(); assert.equal(calls[2].params.offset, 4);
  calls[2].resolve([{ id: 2 }]); await running;
  assert.equal(states.at(-1).hasMore, false);
  await feed.more(); assert.equal(calls.length, 3);
});

test("a failed page retains visible rows and can retry the same offset", async () => {
  const calls = [], states = [];
  const feed = createNotificationFeed((params) => { const pending = deferred(); calls.push({ params, ...pending }); return pending.promise; }, (state) => states.push(state), 1);
  let running = feed.reset(); calls[0].resolve([{ id: 1 }]); await running;
  running = feed.more(); calls[1].reject(new Error("offline")); await running;
  assert.deepEqual(states.at(-1).items, [{ id: 1 }]);
  assert.equal(states.at(-1).error.message, "offline");
  running = feed.more(); assert.equal(calls[2].params.offset, 1);
  calls[2].resolve([]); await running;
  assert.equal(states.at(-1).error, null);
});

test("refresh after deletion or marking read starts at zero; disposal prevents any later publication", async () => {
  const calls = [], states = [];
  const feed = createNotificationFeed((params) => { const pending = deferred(); calls.push({ params, ...pending }); return pending.promise; }, (state) => states.push(state), 1);
  let running = feed.reset("unread"); calls[0].resolve([{ id: 1 }]); await running;
  running = feed.reset("unread");
  assert.equal(calls[1].params.offset, 0);
  assert.deepEqual(states.at(-1).items, []);
  const count = states.length; feed.dispose();
  calls[1].resolve([{ id: 2 }]); await running;
  assert.equal(states.length, count);
});
