import test from "node:test";
import assert from "node:assert/strict";
import { programmingEvidenceRelevant } from "../src/utils/evidenceContext.js";

test("an empty or nontechnical profile keeps programming integrations discreet", () => {
  for (const profile of [null, {}, { profession: "Contadora", skills: ["Excel", "Power BI"] }, { profession: "Psicóloga", preferred_sector: "Tecnologia y software" }, { profession: "Ingeniero industrial", skills: ["Sistemas de gestión de calidad"] }]) {
    assert.equal(programmingEvidenceRelevant(profile), false);
  }
});

test("explicit programming skills and professions make the optional label relevant", () => {
  for (const profile of [{ skills: [" PYTHON "] }, { skills: ["Programación"] }, { skills: ["C++"] }, { profession: "Desarrolladora frontend" }, { profession: "Ingeniero de sistemas" }, { profession: "Ingeniera en informática" }, { profession: "Senior Software Engineer" }]) {
    assert.equal(programmingEvidenceRelevant(profile), true);
  }
});

test("unrelated words do not match programming skill substrings", () => {
  assert.equal(programmingEvidenceRelevant({ profession: "Vendedor", skills: ["Reactores", "Gestión", "Comunicación"] }), false);
});

test("saved technical evidence remains relevant after a change of profession", () => {
  for (const row of [{ analysis: { origin: "github_public" } }, { analysis: { origin: "codewars_public" } }, { kind: "repository" }]) {
    assert.equal(programmingEvidenceRelevant({ profession: "Administradora" }, [row]), true);
  }
  assert.equal(programmingEvidenceRelevant({}, [{ kind: "certificate" }, { kind: "experience" }]), false);
});
