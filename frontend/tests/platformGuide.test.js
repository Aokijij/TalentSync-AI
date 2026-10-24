import assert from "node:assert/strict";
import { test } from "node:test";
import { guideForRole, platformGuide } from "../src/constants/platformGuide.js";
import { practiceBindingPayload, practiceEditorValue } from "../src/utils/practiceAuthoring.js";

test("guide actions follow company permissions and each role keeps a complete local route", () => {
  const interviewer = guideForRole("company", "interviewer");
  assert.deepEqual(interviewer.map((row) => row.id), ["interviews", "security"]);
  assert.ok(guideForRole("company", "recruiter").every((row) => !["verification", "team"].includes(row.id)));
  for (const chapters of Object.values(platformGuide)) for (const chapter of chapters) {
    assert.ok(chapter.to.startsWith("/") && !chapter.to.startsWith("//"));
    assert.ok(chapter.steps.length >= 3 && chapter.note && chapter.summary);
  }
});
test("authored practice preserves a zero answer, multiline pairs and explicit removal of association", () => {
  const binding = { mode: "custom", rationale: "El caso se revisó contra el temario completo.", draft: { title: "Comprueba un resultado", scenario: "Se comparan los datos ficticios del caso.", steps: ["Recibir datos", "Revisar datos", "Registrar resultado"], calculation_prompt: "¿Qué diferencia hay entre dos valores iguales?", calculation_answer: 0, calculation_feedback: "Los dos valores son iguales y su diferencia es cero.", terms: ["Entrada", "Proceso", "Salida"], meanings: ["Dato inicial", "Operación realizada", "Resultado producido"] } };
  assert.deepEqual(practiceBindingPayload(practiceEditorValue(binding)), binding);
  assert.deepEqual(practiceBindingPayload({ ...practiceEditorValue(binding), mode: "none" }), { mode: "none" });
});
