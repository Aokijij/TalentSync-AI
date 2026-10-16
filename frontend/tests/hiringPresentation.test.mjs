import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
async function component(file, name) {
  const compiled = await build({ entryPoints: [fileURLToPath(new URL(`../src/components/${file}.jsx`, import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" } });
  const module = { exports: {} };
  new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
  return module.exports[name];
}

const StructuredJobText = await component("StructuredJobText", "StructuredJobText");
const VacancyPicker = await component("VacancyPicker", "VacancyPicker");
const ScreeningQuestionsEditor = await component("ScreeningQuestionsEditor", "ScreeningQuestionsEditor");
const OfferPublicationStatus = await component("OfferPublicationStatus", "OfferPublicationStatus");
const OfferQualityBreakdown = await component("OfferQualityBreakdown", "OfferQualityBreakdown");
const WorkScheduleEditor = await component("WorkScheduleEditor", "WorkScheduleEditor");

test("inline AI experience bullets render as separate safe list items", () => {
  const html = renderToStaticMarkup(createElement(StructuredJobText, { text: "• Revisé inventarios. • Analicé movimientos. • Registré <script>datos</script>." }));
  assert.equal((html.match(/<li /g) || []).length, 3);
  assert.match(html, /<ul /);
  assert.ok(!html.includes("<script>"));
  assert.match(html, /&lt;script&gt;datos/);
});

test("the vacancy search exposes one labelled combobox with the selected job", () => {
  const html = renderToStaticMarkup(createElement(VacancyPicker, { jobs: [], selected: { id: 7, title: "Analista de datos" }, query: "", onQuery() {}, onSelect() {} }));
  assert.equal((html.match(/<input /g) || []).length, 1);
  assert.ok(!html.includes("<select"));
  assert.match(html, /role="combobox"/);
  assert.match(html, /value="Analista de datos"/);
  assert.match(html, /Buscando para:/);
});

test("question editor renders saved choice scores and open answer controls", () => {
  const value = [{ id: "availability", prompt: "¿Puedes asistir los sábados?", type: "choice", required: true, options: ["Sí", "No"], option_scores: { "Sí": 3, "No": -1 } }, { id: "approach", prompt: "¿Cómo organizarías tus tareas?", type: "open", required: false, options: [] }];
  const html = renderToStaticMarkup(createElement(ScreeningQuestionsEditor, { value, onChange() {} }));
  assert.match(html, /value="3" selected=""/);
  assert.match(html, /value="-1" selected=""/);
  assert.match(html, /¿Cómo organizarías tus tareas\?/);
  assert.match(html, /Respuesta obligatoria/);
});

test("publication status separates the numeric minimum from missing required information", () => {
  const quality = { score: 74, minimum_publish_score: 60, can_publish: false, blockers: [{ label: "Contrato definido" }], issues: [] };
  const html = renderToStaticMarkup(createElement(OfferPublicationStatus, { quality }));
  assert.match(html, /Puntaje suficiente/);
  assert.match(html, /60\/100/);
  assert.match(html, /Contrato definido/);
  const ready = renderToStaticMarkup(createElement(OfferPublicationStatus, { quality: { ...quality, can_publish: true, blockers: [] } }));
  assert.match(ready, /Puedes publicar/);
});

test("quality breakdown shows earned responsibility points independently of missions", () => {
  const html = renderToStaticMarkup(createElement(OfferQualityBreakdown, { quality: { score: 20, checks: [{ key: "description", label: "Responsabilidades", step: 1, points: 20, weight: 20, passed: true, required: true }, { key: "missions", label: "Misiones", step: 1, points: 0, weight: 3, passed: false }] } }));
  assert.match(html, /20\/23/);
  assert.match(html, /20\/20/);
  assert.match(html, /0\/3/);
});

test("schedule editor keeps legacy free text editable", () => {
  const html = renderToStaticMarkup(createElement(WorkScheduleEditor, { details: { schedule: "Sábados de 7:00 a 12:00" }, onChange() {} }));
  assert.match(html, /<textarea/);
  assert.match(html, /Sábados de 7:00 a 12:00/);
  assert.match(html, /Escribir horario/);
});
