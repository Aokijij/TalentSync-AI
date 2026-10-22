import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { preparationText, reviewAnswer } from "../src/utils/preparation.js";

const require = createRequire(import.meta.url);
const compiled = await build({ entryPoints: [fileURLToPath(new URL("../src/components/PreparationWorkspace.jsx", import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" } });
const module = { exports: {} };
new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
const { PreparationWorkspace } = module.exports;
const noop = () => {};
const data = {
  job: { title: "Analista de inventarios", company_name: "Equipo de logística" },
  profile: { summary: "Preparaba reportes", experiences: [{ role: "Auxiliar", company: "Bodega" }], skills: ["excel"] },
  versions: [],
  interview: { questions: [{ id: "introduction", title: "¿Qué experiencia se relaciona con este cargo?", hint: "Elige un ejemplo real", experiences: [] }], ask_company: ["¿Qué esperan en los primeros meses?"], answers: {}, version: 0 },
};
const props = { data, tab: "cv", onTab: noop, form: { summary: "Preparaba reportes", experiences: [0], skills: ["excel"], style: "modern", includePhoto: false }, onForm: noop, answers: {}, onAnswer: noop, questionIndex: 0, onQuestion: noop, onSaveInterview: noop, onDownloadNotes: noop, onCreateVersion: noop, onPreview: noop, onDownload: noop };

test("CV preparation presents saved facts, accessible fields and an honest empty history", () => {
  const html = renderToStaticMarkup(createElement(PreparationWorkspace, props));
  assert.match(html, /Analista de inventarios/);
  assert.match(html, /Auxiliar/);
  assert.match(html, /Todavía no hay versiones guardadas/);
  assert.match(html, /Guardar versión del CV/);
  assert.match(html, /aria-controls="preparation-panel-cv"/);
  assert.match(html, /role="tabpanel" aria-labelledby="preparation-tab-cv"/);
  assert.doesNotMatch(html, /Enviar postulación/);
});

test("interview practice shows missing structure without a candidate score or invented answer", () => {
  const html = renderToStaticMarkup(createElement(PreparationWorkspace, { ...props, tab: "interview", dirty: true, answers: { introduction: { action: "Ordené los registros" } } }));
  assert.match(html, /Ordené los registros/);
  assert.match(html, /Por completar: contexto, responsabilidad, resultado/);
  assert.match(html, /0 de 1 respuestas estructuradas/);
  assert.match(html, /Guardar mis respuestas/);
  assert.doesNotMatch(html, /\d+%|Calificación|aprobado/i);
});

test("submitted document mode exposes the exact chosen version without an editor or replacement action", () => {
  const versions = ["sent", "other"].map((id) => ({ id, created_at: "2026-10-20T12:00:00", skills: ["excel"], experiences: [], style: "modern" }));
  const html = renderToStaticMarkup(createElement(PreparationWorkspace, { ...props, application: true, data: { ...data, versions, submitted_resume_id: "sent" } }));
  assert.equal((html.match(/Ver PDF/g) || []).length, 1);
  assert.match(html, /Documento de esta postulación/);
  assert.doesNotMatch(html, /Guardar versión del CV|Resumen para esta vacante|Usar al postularme/);
});

test("notes export preserves the candidate's exact statements and structure review ignores whitespace", () => {
  const answer = { situation: "  ", task: "Revisar", action: "Ordené", result: "Consultaron el reporte" };
  assert.deepEqual(reviewAnswer(answer), { complete: false, missing: ["Contexto"] });
  const text = preparationText(data.job, data.interview.questions, { introduction: answer });
  assert.match(text, /Acción: Ordené/);
  assert.match(text, /Resultado: Consultaron el reporte/);
  assert.match(text, /Preparación privada/);
  assert.doesNotMatch(text, /Dominio acreditado|Contratado/);
});
