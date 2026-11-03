import test from "node:test";
import assert from "node:assert/strict";
import { buildStarDraft } from "./careerCoach.js";

test("STAR draft uses only supplied facts and supports qualitative results", () => {
  const draft = buildStarDraft({ situation: " Faltaban reportes ", task: "El equipo necesitaba consultar pedidos", action: "Preparé un tablero con Excel", result: "El equipo pudo consultar los pedidos" });
  assert.equal(draft, "Faltaban reportes. El equipo necesitaba consultar pedidos. Preparé un tablero con Excel. El equipo pudo consultar los pedidos.");
  assert.doesNotMatch(draft, /\d|%|lideré|aumenté/i);
});

test("incomplete facts, placeholders and oversized drafts cannot be applied", () => {
  assert.equal(buildStarDraft({ situation: "Problema" }), "");
  assert.equal(buildStarDraft({ situation: "Problema", task: "Objetivo", action: "Acción", result: "[X]%" }), "");
  assert.equal(buildStarDraft({ situation: "a".repeat(3000), task: "b", action: "c", result: "d" }), "");
});
