import assert from "node:assert/strict";
import { test } from "node:test";
import { notifyVacancyMutation, subscribeVacancyChanges } from "./vacancyEvents.js";

test("saved vacancy content and status refresh same-tab and other-tab views without sharing content", () => {
  const surface = new globalThis.EventTarget();
  const written = [];
  surface.localStorage = { setItem: (key, value) => written.push([key, value]) };
  let refreshes = 0;
  const stop = subscribeVacancyChanges("42", () => refreshes++, surface);
  notifyVacancyMutation({ method: "patch", url: "/admin/jobs/42/content" }, surface);
  notifyVacancyMutation({ method: "get", url: "/jobs/42" }, surface);
  notifyVacancyMutation({ method: "post", url: "/jobs/42/match" }, surface);
  notifyVacancyMutation({ method: "patch", url: "/admin/jobs/99/catalog-status" }, surface);
  assert.equal(refreshes, 1);
  assert.deepEqual(Object.keys(JSON.parse(written[0][1])).sort(), ["changedAt", "id", "nonce"]);
  const event = new globalThis.Event("storage");
  Object.assign(event, { key: written[0][0], newValue: written[0][1] });
  surface.dispatchEvent(event);
  assert.equal(refreshes, 2);
  stop();
  surface.dispatchEvent(event);
  assert.equal(refreshes, 2);
});
