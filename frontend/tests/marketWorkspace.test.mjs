import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";

const require = createRequire(import.meta.url);
async function component(path, name) {
  const compiled = await build({ entryPoints: [fileURLToPath(new URL(path, import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" },
    plugins: [{ name: "isolated-render", setup(builder) {
      builder.onResolve({ filter: /api\/client\.js$/ }, () => ({ path: "api", namespace: "test" }));
      builder.onLoad({ filter: /.*/, namespace: "test" }, () => ({ contents: "export const api = {}; export const getApiErrorMessage = () => 'Error';", loader: "js" }));
    } }] });
  const module = { exports: {} };
  new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
  return module.exports[name];
}
const Workspace = await component("../src/components/CareerCoachWorkspace.jsx", "CareerCoachWorkspace");
const Export = await component("../src/components/ResumeExportDialog.jsx", "ResumeExportDialog");
test("market demand uses the filtered report and avoids a second search form", () => {
  const radar = { sample: 7, skills: [{ skill: "typescript", count: 5, declared: false, courses: [] }], jobs: [], sources: {}, note: "Solo ofertas reales", since: "2026-07-16", as_of: "2026-10-14", small_sample: false };
  const html = renderToStaticMarkup(createElement(MemoryRouter, null, createElement(Workspace, { profile: { skills: [] }, context: "learning", externalRadar: radar, hideFilters: true })));
  assert.match(html, /7 ofertas consultadas/);
  assert.match(html, /TypeScript/);
  assert.match(html, /Solo ofertas reales/);
  assert.doesNotMatch(html, /Personaliza tu búsqueda/);
});
test("saved export selections restore without exposing omitted contact or triggering a download", () => {
  const html = renderToStaticMarkup(createElement(Export, { open: true, name: "Candidata", profile: { resume_style: "modern", resume_color: "teal", resume_export_options: { sections: ["summary"], include_photo: false } } }));
  assert.match(html, /Guardar mi diseño/);
  assert.match(html, /Vista previa del PDF/);
  assert.match(html, /type="checkbox" checked=""\/>Resumen profesional/);
  assert.doesNotMatch(html, /type="checkbox" checked=""\/>Datos de contacto/);
  assert.match(html, /disabled=""[^>]*>.*?Descargar este PDF/);
});
