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
const ExperienceRequirementEditor = await component("ExperienceRequirementEditor", "ExperienceRequirementEditor");
const RemoteScopeEditor = await component("RemoteScopeEditor", "RemoteScopeEditor");
const OfferConditions = await component("OfferConditions", "OfferConditions");
const EducationRequirementsEditor = await component("EducationRequirementsEditor", "EducationRequirementsEditor");
const TextItemsEditor = await component("TextItemsEditor", "TextItemsEditor");

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
  const html = renderToStaticMarkup(createElement(OfferQualityBreakdown, { quality: { score: 15, checks: [{ key: "description", label: "Responsabilidades", step: 1, points: 15, weight: 15, passed: true, required: true }, { key: "missions", label: "Misiones", step: 1, points: 0, weight: 9, passed: false }] } }));
  assert.match(html, /70 puntos/);
  assert.match(html, /30 \(30%\)/);
  assert.match(html, /15\/24/);
  assert.match(html, /15\/15/);
  assert.match(html, /0\/9/);
});

test("schedule editor keeps legacy free text editable", () => {
  const html = renderToStaticMarkup(createElement(WorkScheduleEditor, { details: { schedule: "Sábados de 7:00 a 12:00" }, onChange() {} }));
  assert.match(html, /<textarea/);
  assert.match(html, /Sábados de 7:00 a 12:00/);
  assert.match(html, /Escribir horario/);
});

test("structured schedule displays calculated hours and custom time triggers", () => {
  const html = renderToStaticMarkup(createElement(WorkScheduleEditor, { details: { work_schedule: { mode: "fixed", days: ["mon", "tue", "wed", "thu", "fri"], start: "05:30", end: "15:30", break_minutes: 60, notes: "" } }, onChange() {} }));
  assert.match(html, /45 horas semanales/);
  assert.match(html, /Se calculan y guardan automáticamente/);
  assert.equal((html.match(/aria-haspopup="dialog"/g) || []).length, 2);
  assert.ok(!html.includes('type="time"'));
  assert.ok(!html.includes("Usar estas horas"));
});

test("monthly experience and remote restrictions are visible to both editors and candidates", () => {
  const details = { seniority: "junior", experience_months: 6, remote_scope: { mode: "regions", countries: ["CO", "MX"], continents: ["EU"] } };
  const experience = renderToStaticMarkup(createElement(ExperienceRequirementEditor, { details, onChange() {} }));
  assert.match(experience, /6 meses/);
  assert.match(experience, /value="months" selected/);
  const remote = renderToStaticMarkup(createElement(RemoteScopeEditor, { value: details.remote_scope, onChange() {} }));
  assert.match(remote, /Continentes admitidos/);
  assert.match(remote, /Quitar CO/);
  assert.match(remote, /Quitar MX/);
  const publicView = renderToStaticMarkup(createElement(OfferConditions, { job: { modality: "remote", quality_details: details } }));
  assert.match(publicView, /6 meses/);
  assert.match(publicView, /Europa · Colombia · México/);
});

test("education levels appear in one list and secondary education has no career field or ongoing option", () => {
  const props = { level: "secondary", fields: ["Sistemas"], acceptsStudents: true, onChange() {} };
  const secondary = renderToStaticMarkup(createElement(EducationRequirementsEditor, props));
  assert.ok(!secondary.includes("<optgroup"));
  assert.ok(!secondary.includes('value="secondary_in_progress"'));
  assert.ok(!secondary.includes("Carreras o áreas aceptadas"));
  assert.match(secondary, /value="secondary" selected/);
  const technical = renderToStaticMarkup(createElement(EducationRequirementsEditor, { ...props, level: "technical" }));
  assert.match(technical, /value="technical_in_progress" selected/);
  assert.match(technical, /Carreras o áreas aceptadas/);
  assert.match(technical, /Quitar Sistemas/);
});

test("long screening prompts and scored options use wrapping textareas and retain their complete text", () => {
  const prompt = "Describe un trabajo o proyecto donde utilizaste JavaScript para construir formularios accesibles y explica cómo verificaste el resultado con el equipo.";
  const option = "Verificar la fuente, documentar la diferencia y acordar con el equipo la corrección antes de continuar.";
  const html = renderToStaticMarkup(createElement(ScreeningQuestionsEditor, { value: [{ id: "example", prompt, type: "choice", required: true, options: [option, "Continuar sin revisar"], option_scores: { [option]: 3 } }], onChange() {} }));
  assert.equal((html.match(/<textarea /g) || []).length, 3);
  assert.ok(html.includes(prompt));
  assert.ok(html.includes(option));
  assert.match(html, /value="3" selected/);
  assert.match(html, /aria-label="Eliminar pregunta 1"/);
});

test("added text items are individual removable chips rather than a comma-separated input", () => {
  const html = renderToStaticMarkup(createElement(TextItemsEditor, { label: "Habilidades que la empresa enseñará", value: ["SQL", "Excel"], onChange() {} }));
  assert.match(html, /Quitar SQL/);
  assert.match(html, /Quitar Excel/);
  assert.ok(!html.includes('value="SQL,Excel"'));
  assert.match(html, /Añadir o Enter/);
});
