import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { practiceDraft, practiceSeconds, restorePractice, savePractice } from "../src/utils/practiceSession.js";

const require = createRequire(import.meta.url);
const compiled = await build({ entryPoints: [fileURLToPath(new URL("../src/components/ChallengeWorkspace.jsx", import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" } });
const module = { exports: {} };
new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
const { ChallengeWorkspace, ChallengeResult } = module.exports;
const noop = () => {};
const questions = [{ id: "python-default", prompt: "¿Qué firma evita compartir una lista mutable entre llamadas?", choices: ["def f(items=[])", "def f(items=None) y crear la lista dentro", "def f(items=list())"] }, { id: "python-errors", prompt: "¿Qué harías ante un dato inesperado?", choices: ["Validarlo y comunicar el error", "Ignorarlo"] }];
const attempt = { id: "sample", title: "Fundamentos de Python", skill: "python", status: "active", questions };
const props = { attempt, answers: {}, step: 0, seconds: 441, onStep: noop, onAnswer: noop, onExit: noop, onSubmit: noop };

test("practice workspace presents the current question, navigable progress and explicit draft/time behavior", () => {
  const html = renderToStaticMarkup(createElement(ChallengeWorkspace, { ...props, answers: { "python-default": 0 } }));
  assert.match(html, /Espacio de práctica/);
  assert.match(html, /Fundamentos de Python/);
  assert.match(html, /7:21/);
  assert.match(html, /1 de 2 respondidas/);
  assert.match(html, /Pregunta 1: respondida/);
  assert.match(html, /practice-option selected/);
  assert.match(html, /is-code/);
  assert.match(html, /Al salir, el tiempo sigue corriendo/);
  assert.doesNotMatch(html, /¿Qué harías ante un dato inesperado\?/);
});

test("review shows unanswered items, supports editing and prevents incomplete delivery", () => {
  const html = renderToStaticMarkup(createElement(ChallengeWorkspace, { ...props, step: 2, answers: { "python-default": 1 } }));
  assert.match(html, /Revisa tus respuestas/);
  assert.match(html, /Te falta 1 pregunta/);
  assert.match(html, /Sin responder/);
  assert.match(html, /Responder.*pregunta 2/s);
  assert.match(html, /class="button-primary" disabled=""/);
  const complete = renderToStaticMarkup(createElement(ChallengeWorkspace, { ...props, step: 2, answers: { "python-default": 1, "python-errors": 0 } }));
  assert.doesNotMatch(complete, /class="button-primary" disabled=""/);
});

test("expired or pending requests cannot submit and errors keep the chosen answers visible", () => {
  const html = renderToStaticMarkup(createElement(ChallengeWorkspace, { ...props, step: 2, seconds: 0, answers: { "python-default": 1, "python-errors": 0 }, error: "No pudimos completar la entrega" }));
  assert.match(html, /El tiempo de este intento terminó/);
  assert.match(html, /Tus respuestas siguen disponibles/);
  assert.match(html, /def f\(items=None\)/);
  assert.match(html, /class="button-primary" disabled=""/);
  const pending = renderToStaticMarkup(createElement(ChallengeWorkspace, { ...props, busy: true }));
  assert.match(pending, /type="radio"[^>]*disabled=""/);
});

test("results expose incorrect explanations immediately and keep correct answers expandable", () => {
  const html = renderToStaticMarkup(createElement(ChallengeResult, { attempt: { ...attempt, status: "completed", score: 50, passed: false, feedback: [{ question_id: "python-default", prompt: questions[0].prompt, correct: false, message: "La lista predeterminada se comparte entre llamadas." }, { question_id: "python-errors", prompt: questions[1].prompt, correct: true, message: "Valida los datos antes de usarlos." }] }, onExit: noop, onResults: noop }));
  assert.match(html, /1 de 2 respuestas correctas/);
  assert.match(html, /<details open="">/);
  assert.equal((html.match(/<details open="">/g) || []).length, 1);
  assert.match(html, /La lista predeterminada se comparte/);
  assert.match(html, /Ver mis resultados/);
});

test("timer accepts UTC with and without suffix, handles offsets and stops at expiry", () => {
  const now = Date.parse("2026-10-22T16:00:00Z");
  assert.equal(practiceSeconds("2026-10-22T16:07:21", now), 441);
  assert.equal(practiceSeconds("2026-10-22T16:07:21Z", now), 441);
  assert.equal(practiceSeconds("2026-10-22T11:07:21-05:00", now), 441);
  assert.equal(practiceSeconds("2026-10-22T15:59:59Z", now), 0);
  assert.equal(practiceSeconds("invalid", now), 0);
});

test("draft restoration preserves choice zero and discards malformed data without crashing inputs", () => {
  const draft = practiceDraft({ "python-default": 0, "python-errors": "0", other: 2 }, questions);
  assert.deepEqual(draft, { "python-default": 0 });
  assert.deepEqual(practiceDraft(null, questions), {});
  const restored = restorePractice({ getItem: () => '{"python-default":1}' }, "draft", questions);
  assert.equal(restored.answers["python-default"], 1);
  assert.equal(restored.warning, "");
  for (const raw of ["broken", "null", "[]"]) assert.match(restorePractice({ getItem: () => raw }, "draft", questions).warning, /No pudimos recuperar/);
});

test("unavailable storage reports a warning instead of losing the live answers to an exception", () => {
  const denied = { getItem() { throw new Error("blocked"); }, setItem() { throw new Error("quota"); } };
  assert.match(restorePractice(denied, "draft", questions).warning, /No pudimos recuperar/);
  assert.match(savePractice(denied, "draft", { "python-default": 1 }), /no permite guardar/);
});

test("exercise drafts preserve partial matching and numeric results while rejecting invalid ordering", () => {
  const typed = [{ id: "order", type: "order", choices: ["A", "B", "C"] }, { id: "matching", type: "matching", terms: ["A", "B"], choices: ["One", "Two"] }, { id: "number", type: "number", choices: [] }, { id: "multi", type: "multi_select", choices: ["A", "B", "C"] }];
  assert.deepEqual(practiceDraft({ order: [1, 0, 2], matching: [-1, 0], number: "0", multi: [0, 2] }, typed), { order: [1, 0, 2], matching: [-1, 0], number: "0", multi: [0, 2] });
  assert.deepEqual(practiceDraft({ order: [0, 0, 0], matching: "bad", number: "Infinity", multi: [999] }, typed), {});
});
