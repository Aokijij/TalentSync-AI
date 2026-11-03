import assert from "node:assert/strict";
import test from "node:test";
import { DEFAULT_API_URL, resolveApiBase } from "../src/api/config.js";

test("production keeps authentication on its own origin when no safe API is configured", () => {
  for (const configured of [undefined, "", "http://127.0.0.1:8000/api/v1", "https://localhost/api/v1", "https://[::1]/api/v1", "http://api.example.test/api/v1", "//api.example.test/api/v1", "https://user:password@api.example.test/api/v1", "javascript:alert(1)"]) {
    assert.equal(resolveApiBase(configured, { hostname: "talentsync-ai.pages.dev" }), DEFAULT_API_URL);
  }
});

test("same-origin routes and an explicitly configured HTTPS API are preserved", () => {
  for (const hostname of ["talentsync-ai.pages.dev", "api.example.test"]) {
    assert.equal(resolveApiBase("/api/v1", { hostname }), "/api/v1");
    assert.equal(resolveApiBase("https://api.example.test/api/v1/", { hostname }), "https://api.example.test/api/v1");
  }
});

test("local development can still use its isolated API", () => {
  for (const hostname of ["localhost", "127.0.0.1", "::1"]) {
    assert.equal(resolveApiBase("http://127.0.0.1:8000/api/v1", { hostname }), "http://127.0.0.1:8000/api/v1");
    assert.equal(resolveApiBase("", { hostname }), "/api/v1");
  }
});
