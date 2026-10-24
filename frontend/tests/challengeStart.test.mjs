import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
const compiled = await build({ entryPoints: [fileURLToPath(new URL("../src/components/ChallengeCatalog.jsx", import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" } });
const module = { exports: {} };
new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
const { ChallengeCatalog } = module.exports;
const { latestChallengeAttempt } = await import("../src/utils/learningChallenges.js");
const noop = () => {};
const now = Date.parse("2026-10-22T16:00:00Z");
const assessments = ["python", "sql", "microservices"].map((skill) => ({ id: skill, skill, title: `Práctica de ${skill}`, category: "technology", minutes: 10 }));
const render = (attempt) => renderToStaticMarkup(createElement(MemoryRouter, {}, createElement(ChallengeCatalog, { assessments, areas: [{ id: "technology", label: "Tecnología y datos" }], attempt, now, onStart: noop, onReview: noop, onExplore: noop })));

test("starting or resuming an active practice keeps the catalog visible and disables only the other practices", () => {
  const html = render({ id: "active-python", assessment_id: "python", status: "active", started_at: "2026-10-22T15:59:00", expires_at: "2026-10-22T16:09:00", questions: [] });
  assert.match(html, /Continuar práctica/);
  assert.match(html, /Práctica de sql/);
  assert.match(html, /Práctica de microservices/);
  assert.equal((html.match(/<button[^>]*id="challenge-start-[^"]+"[^>]*disabled=""/g) || []).length, 2);
});

test("a locally expired practice does not block starting a different practice", () => {
  const html = render({ id: "expired-python", assessment_id: "python", status: "active", started_at: "2026-10-21T15:59:00Z", expires_at: "2026-10-21T16:09:00Z" });
  assert.equal((html.match(/<button[^>]*id="challenge-start-[^"]+"[^>]*disabled=""/g) || []).length, 0);
  assert.match(html, /Empezar práctica/);
});

test("reviewing a historical result does not replace a newer active catalog attempt", () => {
  const active = { id: "new", assessment_id: "python", status: "active", version: 1, started_at: "2026-10-22T15:59:00Z", expires_at: "2026-10-22T16:09:00Z" };
  const historical = { id: "old", assessment_id: "python", status: "completed", score: 100, started_at: "2026-10-20T15:59:00Z" };
  assert.equal(latestChallengeAttempt({ id: "python", last_attempt: active }, historical), active);
  const html = renderToStaticMarkup(createElement(ChallengeCatalog, { assessments: [{ ...assessments[0], last_attempt: active }], areas: [], attempt: historical, now, onStart: noop, onReview: noop, onExplore: noop }));
  assert.match(html, /Continuar práctica/);
  assert.doesNotMatch(html, /Último resultado/);
});

test("completion of the same attempt supersedes the catalog copy without reviving an older version", () => {
  const active = { id: "same", assessment_id: "python", status: "active", version: 1 };
  const completed = { ...active, status: "completed", version: 2, score: 80 };
  assert.equal(latestChallengeAttempt({ id: "python", last_attempt: active }, completed), completed);
  assert.equal(latestChallengeAttempt({ id: "python", last_attempt: completed }, active), completed);
});
