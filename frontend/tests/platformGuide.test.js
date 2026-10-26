import assert from "node:assert/strict";
import { test } from "node:test";
import { guideForRole, platformGuide, searchGuideTopics } from "../src/constants/platformGuide.js";
import { navigationLinks } from "../src/constants/navigation.js";
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

test("guide explains discovery tools separately and search respects role permissions", () => {
  const candidate = guideForRole("candidate");
  assert.equal(candidate.length, 15);
  for (const id of ["quality", "compare", "saved", "compatibility", "calendar", "skills"]) {
    const row = candidate.find((item) => item.id === id);
    assert.ok(row.explains.length >= 2 && row.steps.length >= 3);
  }
  assert.ok(searchGuideTopics(candidate, "calidad ofertas").some((row) => row.id === "quality"));
  assert.ok(searchGuideTopics(candidate, "comparación").some((row) => row.id === "compare"));
  assert.deepEqual(searchGuideTopics(candidate, "noexistefuncion"), []);
  assert.ok(!searchGuideTopics(guideForRole("company", "interviewer"), "publicar una oferta").some((row) => row.id === "offers"));
  for (const role of ["candidate", "company", "admin"]) {
    const chapters = guideForRole(role);
    assert.equal(new Set(chapters.map((row) => row.id)).size, chapters.length);
    assert.equal(new Set(chapters.map((row) => row.icon)).size, chapters.length);
    assert.ok(chapters.every((row) => row.group && row.to.startsWith("/") && !row.to.startsWith("//")));
  }
  assert.doesNotMatch(candidate.find((row) => row.id === "results").steps.join(" "), /alterna Prácticas/);
});

test("each role has distinct navigation icons and routes", () => {
  for (const role of ["candidate", "company", "admin"]) {
    const items = navigationLinks.filter((row) => row.roles.includes(role));
    assert.equal(new Set(items.map((row) => row.icon)).size, items.length);
    assert.equal(new Set(items.map((row) => row.to)).size, items.length);
    assert.ok(items.some((row) => row.to === "/guia"));
  }
});
test("authored practice preserves a zero answer, multiline pairs and explicit removal of association", () => {
  const binding = { mode: "custom", rationale: "El caso se revisó contra el temario completo.", draft: { title: "Comprueba un resultado", scenario: "Se comparan los datos ficticios del caso.", steps: ["Recibir datos", "Revisar datos", "Registrar resultado"], calculation_prompt: "¿Qué diferencia hay entre dos valores iguales?", calculation_answer: 0, calculation_feedback: "Los dos valores son iguales y su diferencia es cero.", terms: ["Entrada", "Proceso", "Salida"], meanings: ["Dato inicial", "Operación realizada", "Resultado producido"] } };
  assert.deepEqual(practiceBindingPayload(practiceEditorValue(binding)), binding);
  assert.deepEqual(practiceBindingPayload({ ...practiceEditorValue(binding), mode: "none" }), { mode: "none" });
});
