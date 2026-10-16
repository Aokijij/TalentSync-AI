import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
async function component(name) {
  const compiled = await build({
    entryPoints: [fileURLToPath(new URL(`../src/components/${name}.jsx`, import.meta.url))],
    bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external",
    plugins: [{ name: "no-api-in-render", setup(builder) {
      builder.onLoad({ filter: /\.css$/ }, () => ({ contents: "", loader: "js" }));
      builder.onResolve({ filter: /api\/client\.js$/ }, () => ({ path: "api", namespace: "test" }));
      builder.onLoad({ filter: /.*/, namespace: "test" }, () => ({ contents: "export const api = {}; export const getApiErrorMessage = () => '';", loader: "js" }));
    } }],
  });
  const module = { exports: {} };
  new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
  return module.exports[name];
}

test("company explanation shows factors, levels, years and months and private response adjustment", async () => {
  const Panel = await component("CandidateMatchExplanation");
  const html = renderToStaticMarkup(createElement(Panel, { match: {
    professional_match_percentage: 80, base_match_percentage: 72, match_percentage: 74, screening_adjustment: 2, location_fit: { factor: 0.9, message: "Disponibilidad por confirmar" },
    match_details: { components: [{ key: "skills", label: "Habilidades", score: 70, points: 35, weight: 0.5 }], experience_requirement: { related_months: 45, required_months: 36 }, requirements: [{ key: "python", skill: "python", status_label: "Cumplimiento parcial", required_level: "advanced", declared_level: "basic", reason: "Revisa el nivel solicitado." }] },
  } }));
  for (const value of ["¿Por qué tiene esta compatibilidad?", "3 años y 9 meses", "Avanzado", "Básico", "+2", "74%", "35.0 puntos", "Disponibilidad por confirmar"]) assert.ok(html.includes(value), value);
  assert.ok(!html.includes("3.75"));
});

test("audit report explains its purpose and keeps technical identifiers in a disclosure", async () => {
  const Panel = await component("EngineAuditPanel");
  const html = renderToStaticMarkup(createElement(Panel, { busy: false, onRun: () => {}, audits: [{ id: 1, version: "private-support-version", created_at: "2026-10-15T12:00:00", metrics: { pair_count: 200, identity_invariance_violations: 10, distribution_psi: null } }] }));
  for (const value of ["¿Cuándo usarla?", "Hay resultados que necesitan revisión", "200 comparaciones", "revisión técnica", "Datos para soporte técnico"]) assert.ok(html.includes(value), value);
  assert.match(html, /<details><summary[^>]*>Datos para soporte técnico/);
});

test("course batch import starts with a documented example and preview before saving", async () => {
  const Panel = await component("CourseBatchImport");
  const html = renderToStaticMarkup(createElement(Panel, { onImported: () => {} }));
  for (const value of ["Descargar ejemplo", "Seleccionar archivo JSON", "Revisar antes de importar", "borradores", "Qué significa cada campo", "details.level"]) assert.ok(html.includes(value), value);
  assert.ok(!html.includes("Importar 1 borradores"));
});

test("skill editor has one accessible level selector and explains conservative CV defaults", async () => {
  const Panel = await component("SkillLevelsEditor");
  const html = renderToStaticMarkup(createElement(Panel, { editing: true, skills: ["python", "sql"], levels: { python: "learning" }, sources: { python: { source: "default", level: "learning" } }, onChange: () => {}, onRemove: () => {} }));
  assert.equal((html.match(/role="radio"/g) || []).length, 5);
  for (const value of ["Buscar habilidad", "Nivel de python", "El CV no indica un nivel claro", "Quitar habilidad python", "En aprendizaje"]) assert.ok(html.includes(value), value);
  assert.ok(!html.includes("<select"));
});

test("discarded CV mentions expose deletion separately from recovery", async () => {
  const Panel = await component("CvContextReview");
  const html = renderToStaticMarkup(createElement(Panel, { rows: [{ skill: "sql", state: "learning", excerpt: "Aprendiendo SQL" }], decisions: { sql: "dismissed" }, onDecision: () => {} }));
  assert.ok(html.includes("Eliminar mención descartada de sql") && html.includes("Recuperar"));
});

test("requirement support opens a dialog instead of expanding the vacancy card", async () => {
  const Panel = await component("RequirementSupport");
  const html = renderToStaticMarkup(createElement(Panel, { details: { requirements: [{ key: "python", skill: "python", reason: "Private detail" }] } }));
  assert.ok(html.includes('aria-haspopup="dialog"') && html.includes("Ver cumplimiento por requisito"));
  assert.ok(!html.includes("Private detail") && !html.includes("<details"));
});

test("language editor keeps long levels inside consistent controls", async () => {
  const Panel = await component("LanguagesEditor");
  const html = renderToStaticMarkup(createElement(Panel, { value: [{ name: "inglés", level: "B2" }], onChange: () => {} }));
  assert.ok(html.includes("language-fields") && html.includes("language-level-control"));
  assert.ok(html.includes('title="B2 · Intermedio alto"'));
});

test("professional summary exposes personal editing and local generation without changing the saved text", async () => {
  const Panel = await component("ProfessionalSummary");
  const profile = { experience: "Mi texto personal", summary_mode: "custom" };
  const html = renderToStaticMarkup(createElement(Panel, { profile, editing: false, onChange: () => {}, onEdit: () => {} }));
  for (const value of ["Editar mi texto", "Generar con IA local", "Mi texto personal", 'aria-haspopup="dialog"']) assert.ok(html.includes(value));
  assert.ok(!html.includes("<textarea"));
  const editor = renderToStaticMarkup(createElement(Panel, { profile, editing: true, onChange: () => {}, onEdit: () => {} }));
  assert.ok(editor.includes('maxLength="3000"') && editor.includes("Mi texto personal") && editor.includes("Guardar cambios"));
});
