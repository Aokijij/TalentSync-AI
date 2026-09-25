import assert from "node:assert/strict";
import test from "node:test";

import {
  PRODUCTION_API_URL,
  resolveApiBase,
} from "../src/api/config.js";

test("Cloudflare never points authentication to the visitor's localhost", () => {
  assert.equal(
    resolveApiBase("http://127.0.0.1:8000/api/v1", {
      hostname: "talentsync-ai.pages.dev",
    }),
    PRODUCTION_API_URL,
  );
  assert.equal(
    resolveApiBase("/api/v1", { hostname: "talentsync-ai.pages.dev" }),
    PRODUCTION_API_URL,
  );
});

test("local development and the all-in-one Azure image keep their own API route", () => {
  assert.equal(
    resolveApiBase("http://127.0.0.1:8000/api/v1", {
      hostname: "localhost",
    }),
    "http://127.0.0.1:8000/api/v1",
  );
  assert.equal(
    resolveApiBase("/api/v1", {
      hostname: "talentsync-3c02d6e1.eastus2.azurecontainerapps.io",
    }),
    "/api/v1",
  );
});
