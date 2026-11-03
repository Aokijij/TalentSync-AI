import assert from "node:assert/strict";
import { test } from "node:test";
import { detectedRequirements, publicationLabel, qualityColor } from "../src/utils/offerPresentation.js";

test("detected requirements preserve context and exclude existing or duplicate skills", () => {
  assert.deepEqual(detectedRequirements({ requirements: [{ skill: "Excel", essential: true, level: "advanced" }, { skill: "excel" }, { skill: "SAP" }, { skill: "SQL" }] }, [{ skill: "sql" }]), [
    { skill: "Excel", essential: true, level: "advanced", weight: 1 },
    { skill: "SAP", essential: false, level: "basic", weight: 1 },
  ]);
  assert.deepEqual(detectedRequirements({ skills: ["python"] }), [{ skill: "python", essential: false, level: "basic", weight: 1 }]);
});

test("quality color follows the score band independently of publication requirements", () => {
  for (const score of [91, 94, 100]) for (const can_publish of [true, false]) {
    assert.equal(qualityColor({ score, can_publish, level: can_publish ? "A" : "B", rating: { code: "A" } }), "is-complete");
  }
  assert.equal(qualityColor({ score: 86 }), "is-ready");
  assert.equal(publicationLabel("active", true), "Publicada");
  assert.equal(publicationLabel("active", false), "Publicada");
  assert.equal(publicationLabel("draft", true), "Lista para publicar");
  assert.equal(publicationLabel("draft", false), "Revisa los datos pendientes");
  assert.equal(publicationLabel("paused", true), "Pausada");
});
