import test from "node:test";
import assert from "node:assert/strict";
import { shouldNotifyMutation, mutationMessage } from "./feedback.js";

test("navigation calculations and background presence never announce saved changes", () => {
  for (const config of [{}, { method: "get", url: "/jobs" }, { method: "post", url: "/jobs/4/match" }, { method: "post", url: "/hiring/quality/preview" }, { method: "post", url: "/auth/session/company/login" }, { method: "post", url: "/interviews/rooms/2/presence" }, { method: "put", url: "/profiles/me", __quiet: true }]) assert.equal(shouldNotifyMutation(config), false);
  for (const method of ["post", "PUT", "patch", "delete"]) assert.equal(shouldNotifyMutation({ method, url: "/applications" }), true);
});


test("previews downloads and searches never claim changes were saved", () => {
  for (const url of ["/profiles/me/export", "/profiles/me/export/preview", "/hiring/skills/search", "/admin/learning/sources/youtube/preview", "/profiles/me/summary/generate", "/interviews/rooms/7/participants/2/signal"]) assert.equal(shouldNotifyMutation({ method: "post", url }), false, url);
});
test("write feedback describes the actual operation and supports explicit copy", () => {
  assert.match(mutationMessage({ method: "POST", url: "/applications" }), /Postulación enviada/);
  assert.match(mutationMessage({ method: "put", url: "/profiles/me" }), /Perfil actualizado/);
  assert.equal(mutationMessage({ method: "post", url: "/unknown-command" }), "Operación completada.");
  assert.equal(mutationMessage({ __successMessage: "Preferencias guardadas" }, { message: "Other" }), "Preferencias guardadas");
});
