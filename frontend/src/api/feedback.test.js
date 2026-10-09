import test from "node:test";
import assert from "node:assert/strict";
import { shouldNotifyMutation } from "./feedback.js";

test("navigation calculations and background presence never announce saved changes", () => {
  for (const config of [{}, { method: "get", url: "/jobs" }, { method: "post", url: "/jobs/4/match" }, { method: "post", url: "/auth/session/company/login" }, { method: "post", url: "/interviews/rooms/2/presence" }, { method: "put", url: "/profiles/me", __quiet: true }]) assert.equal(shouldNotifyMutation(config), false);
  for (const method of ["post", "PUT", "patch", "delete"]) assert.equal(shouldNotifyMutation({ method, url: "/applications" }), true);
});
