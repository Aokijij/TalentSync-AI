import assert from "node:assert/strict";
import { test } from "node:test";
import { loadAppFont } from "./fontLoading.js";

test("remote font styles cannot block rendering before they finish and are requested only once", () => {
  const links = [], events = {};
  const document = { getElementById: () => links[0], createElement: () => ({ addEventListener: (name, handler) => { events[name] = handler; } }), head: { append: (link) => links.push(link) } };
  loadAppFont(document);
  assert.equal(links[0].rel, "preload");
  assert.equal(links[0].as, "style");
  loadAppFont(document);
  assert.equal(links.length, 1);
  events.load();
  assert.equal(links[0].rel, "stylesheet");
});
