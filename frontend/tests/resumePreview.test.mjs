import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
const compiled = await build({
  entryPoints: [fileURLToPath(new URL("../src/components/ResumePreview.jsx", import.meta.url))],
  bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external",
  plugins: [{ name: "no-network-in-render", setup(builder) {
    builder.onResolve({ filter: /api\/client\.js$/ }, () => ({ path: "api", namespace: "test" }));
    builder.onLoad({ filter: /.*/, namespace: "test" }, () => ({ contents: "export const api = {};", loader: "js" }));
  } }],
});
const module = { exports: {} };
new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
const { ResumePreview } = module.exports;

for (const style of ["classic", "modern", "minimal"]) {
  test(`preview renders ${style} without editor state, including every skill`, () => {
    const skills = Array.from({ length: 18 }, (_, i) => `Habilidad ${i + 1}`);
    const html = renderToStaticMarkup(createElement(ResumePreview, {
      name: "Persona de prueba", email: "prueba@example.com", photoVersion: 0,
      profile: { resume_style: style, skills, experiences: [{ role: "Asesora", company: "Equipo", description: "Atendí solicitudes", start_year: "2022", end_year: "2024" }], educations: [{ degree: "Técnica", institution: "Instituto", start_year: "2025", end_year: "Presente" }], languages: [{ name: "inglés", level: "B1" }] },
    }));
    assert.match(html, /Persona de prueba/);
    assert.match(html, /Atendí solicitudes/);
    assert.match(html, /En curso/);
    for (const skill of skills) assert.ok(html.includes(skill));
    assert.match(html, /bg-white text-slate-900/);
  });
}
