import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { answerAdjustment, applicationBaseMatch, mergeApplicationMatch, projectedMatch } from "../src/utils/applicationMatch.js";

const require = createRequire(import.meta.url);
async function component(file, name) {
  const compiled = await build({ entryPoints: [fileURLToPath(new URL(`../src/components/${file}.jsx`, import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" }, plugins: [{ name: "no-api", setup(builder) {
    builder.onResolve({ filter: /api\/client\.js$/ }, () => ({ path: "api", namespace: "test" }));
    builder.onLoad({ filter: /.*/, namespace: "test" }, () => ({ contents: "export const api = {}; export const getApiErrorMessage = () => '';", loader: "js" }));
  } }] });
  const module = { exports: {} };
  new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
  return module.exports[name];
}
const Workspace = await component("ProcessWorkspace", "ProcessWorkspace");
const Answers = await component("ApplicationAnswersModal", "ApplicationAnswersModal");
const StructuredJobText = await component("StructuredJobText", "StructuredJobText");
const processTime = await component("ProcessWorkspace", "processTime");
const process = { application_id: 5, job_id: 12, company_name: "Empresa ejemplo", candidate_name: "Persona ejemplo", status: "technical_interview", stage_title: "Entrevista técnica", response_days: 3, created_at: "2026-10-18T18:00:00", response_due_at: "2026-10-25T15:00:00", can_evaluate: true, events: [{ id: 1, type: "application.feedback_shared", source: "company", at: "2026-10-22T14:00:00" }], job_description: "Trabajarás con el equipo. Responsabilidades: • Implementar integraciones. • Documentar decisiones.", job_requirements: "Experiencia con Python y SQL." };
const render = (Component, props) => renderToStaticMarkup(createElement(Component, props));

test("process opens a concise overview and keeps other tab panels mounted but hidden", () => {
  const html = render(Workspace, { process, role: "company", evaluation: createElement("textarea", { name: "private-draft", defaultValue: "Evidencia aún sin guardar" }), communication: createElement("form", {}, "Comunicación pendiente") });
  assert.equal((html.match(/role="tab"/g) || []).length, 5);
  assert.match(html, /id="process-tab-overview"[^>]*aria-selected="true"/);
  assert.match(html, /id="process-panel-evaluation"[^>]*hidden=""><textarea name="private-draft">Evidencia aún sin guardar/);
  assert.match(html, /id="process-panel-communicate"[^>]*hidden=""><form>Comunicación pendiente/);
  const overview = html.split('id="process-panel-overview"')[1].split('id="process-panel-vacancy"')[0];
  assert.match(overview, /Próxima respuesta|Registrar evaluación/);
  assert.doesNotMatch(overview, /<textarea|Feedback compartido|Implementar integraciones/);
});

test("candidate view omits private evaluation and employer communication sections", () => {
  const html = render(Workspace, { process, role: "candidate", evaluation: "NOTAS PRIVADAS", preparation: createElement("button", {}, "Preparación privada") });
  assert.equal((html.match(/role="tab"/g) || []).length, 3);
  assert.match(html, /La vacante|Preparación privada/);
  assert.doesNotMatch(html, /NOTAS PRIVADAS|Evaluación interna|Comunicar avance|Persona ejemplo/);
});

test("closed process stops advertising a future response deadline", () => {
  const html = render(Workspace, { process: { ...process, status: "hired", released_at: "2026-10-22T18:00:00" }, role: "candidate" });
  assert.match(html, /Proceso finalizado/);
  assert.doesNotMatch(html, /Próxima respuesta|25 oct/);
});

test("inline responsibilities become a heading and separate escaped list items", () => {
  const html = render(StructuredJobText, { text: `${process.job_description} • Registrar <script>datos</script>.` });
  assert.equal((html.match(/<li /g) || []).length, 3);
  assert.match(html, />Responsabilidades<\/h3>/);
  assert.match(html, /&lt;script&gt;datos/);
  assert.doesNotMatch(html, /<script>/);
  const inline = render(StructuredJobText, { text: "Responsabilidades: Revisar los registros.\nRequisitos: Experiencia relacionada." });
  assert.equal((inline.match(/<h3 /g) || []).length, 2);
});

test("UTC API times display consistently in Colombia, and missing dates have an explicit fallback", () => {
  assert.match(processTime("2026-10-23T14:00:00"), /9:00/);
  assert.equal(processTime("2026-10-23T14:00:00"), processTime("2026-10-23T09:00:00-05:00"));
  assert.equal(processTime("invalid"), "Sin plazo activo");
});

test("an explanation hydrates the live application without overwriting pending answer edits or version", () => {
  const original = { id: 1, version: 8, screening_adjustment: 5, screening_answer_adjustments: { first: 3 }, recruiter_notes: "Borrador", base_match_percentage: null };
  const next = mergeApplicationMatch(original, { base_match_percentage: 63, match_percentage: 68, screening_adjustment: 5 });
  assert.equal(next.base_match_percentage, 63);
  assert.equal(next.adjusted_match_percentage, 68);
  assert.equal(next.version, 8);
  assert.deepEqual(next.screening_answer_adjustments, { first: 3 });
  assert.equal(next.recruiter_notes, "Borrador");
  assert.equal(original.base_match_percentage, null);
});

test("answer review projects from the base rather than adding points twice to an adjusted score", () => {
  const application = { id: 1, screening_answers: [{ question_id: "first", question: "Evidencia", answer: "Ejemplo", type: "open", reviewer_adjustment: 3 }, { question_id: "choice", type: "choice", configured_adjustment: 2, answer: "Sí" }], screening_adjustment: 5 };
  const loaded = mergeApplicationMatch(application, { base_match_percentage: 63, match_percentage: 68 });
  const html = render(Answers, { application: loaded, onClose() {} });
  assert.match(html, /63%/);
  assert.match(html, /68%/);
  assert.match(html, /\+5 pts/);
  assert.doesNotMatch(html, /73%|Sin cálculo/);
});

test("unavailable compatibility is not silently shown as zero, while a genuine zero remains valid", () => {
  assert.equal(applicationBaseMatch({ match_percentage: 70 }), null);
  assert.equal(applicationBaseMatch({ base_match_percentage: "invalid" }), null);
  assert.equal(applicationBaseMatch({ base_match_percentage: 0 }), 0);
  assert.equal(projectedMatch(null, 5), null);
  assert.equal(projectedMatch(0, 5), 5);
  const html = render(Answers, { application: { id: 1, screening_answers: [] }, onClose() {} });
  assert.match(html, /Calculando…/);
  assert.doesNotMatch(html, /0%|Sin cálculo/);
});

test("projection bounds and choice scoring cannot be changed by extraneous manual adjustments", () => {
  const answers = [{ question_id: "first", type: "open", configured_adjustment: 0 }, { question_id: "choice", type: "choice", configured_adjustment: 2 }];
  assert.equal(answerAdjustment(answers, { first: 3, choice: 3, orphan: 3 }), 5);
  assert.equal(projectedMatch(98, 5), 100);
  assert.equal(projectedMatch(2, -5), 0);
  assert.equal(answerAdjustment(Array.from({ length: 10 }, (_, question_id) => ({ question_id, type: "choice", configured_adjustment: 5 }))), 20);
});
