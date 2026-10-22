import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
async function component(name, exportName = name, folder = "components") {
  const compiled = await build({
    entryPoints: [fileURLToPath(new URL(`../src/${folder}/${name}.jsx`, import.meta.url))],
    bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external",
    plugins: [{ name: "no-api-in-render", setup(builder) {
      builder.onLoad({ filter: /\.css$/ }, () => ({ contents: "", loader: "js" }));
      builder.onResolve({ filter: /api\/client\.js$/ }, () => ({ path: "api", namespace: "test" }));
      builder.onLoad({ filter: /.*/, namespace: "test" }, () => ({ contents: "export const api = {}; export const getApiErrorMessage = () => '';", loader: "js" }));
    } }],
  });
  const module = { exports: {} };
  new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
  return module.exports[exportName];
}

test("vacancy training starts as a native closed disclosure with an accessible summary", async () => {
  const Panel = await component("VacancyLearningPanel");
  const html = renderToStaticMarkup(createElement(Panel, { jobId: 1 }));
  const opening = html.match(/^<details[^>]*>/)?.[0];
  assert.ok(opening);
  assert.doesNotMatch(opening, /\bopen(?:=|\s|>)/);
  assert.match(html, /<summary[^>]*>/);
  assert.match(html, /Formación para reforzar tu perfil/);
  assert.match(html, /vacancy-learning-content/);
});

test("language summaries distinguish a CEFR level from native proficiency and keep requested levels explicit", async () => {
  const Panel = await component("LanguagesEditor");
  const value = [{ name: "inglés", level: "B1" }, { name: "español", level: "NATIVE" }];
  const html = renderToStaticMarkup(createElement(Panel, { value, editing: false }));
  for (const text of ["inglés", "B1", "Intermedio", "español", "Nativo"]) assert.ok(html.includes(text));
  assert.equal((html.match(/class="is-filled"/g) || []).length, 3);
  assert.doesNotMatch(html, /role="combobox"/);
  assert.match(html, /Niveles declarados en el perfil/);
  const requested = renderToStaticMarkup(createElement(Panel, { value, editing: false, required: true }));
  assert.match(requested, /Nivel mínimo solicitado para el cargo/);
});

test("the vacancy picker shows provided application counts and sector and distinguishes unavailable counts from zero", async () => {
  const Picker = await component("CompanyApplicationsPage", "JobPickerModal", "pages");
  const html = renderToStaticMarkup(createElement(Picker, { selectedId: "1", jobs: [{ id: 1, title: "Analista de inventario", sector: "Logística", applications_count: 7, status: "active" }, { id: 2, title: "Auxiliar", sector: "Servicios", applications_count: 0, status: "draft" }, { id: 3, title: "Vacante por cargar", sector: "Construcción", status: "paused" }] }));
  assert.match(html, /Logística/);
  assert.match(html, />7</);
  assert.match(html, />0</);
  assert.match(html, /Borrador/);
  assert.match(html, /—/);
  assert.doesNotMatch(html, /Sin sector/);
});

test("demand cards identify published coverage and missing resources and show the proportion of the sample", async () => {
  const Card = await component("LearningDemand", "DemandSkillCard");
  const html = renderToStaticMarkup(createElement(Card, { selected: true, total: 200, row: { skill: "excel", vacancies: 100, companies: 20, published_resources: 1 } }));
  assert.match(html, /50% de la muestra/);
  assert.match(html, /1 recurso publicado/);
  assert.match(html, /aria-pressed="true"/);
  const empty = renderToStaticMarkup(createElement(Card, { total: 200, row: { skill: "logística", vacancies: 25, companies: 10, published_resources: 0 } }));
  assert.match(empty, /Por cubrir en el catálogo/);
});

test("vacancy course cards name the missing skills they reinforce instead of listing unrelated course tags", async () => {
  const Card = await component("LearningResourceCard");
  const html = renderToStaticMarkup(createElement(Card, { compact: true, resource: { id: "excel", title: "Cruza datos de inventario", category: "administration", hours: 8, cost: "free", skills: ["excel", "power query"], targeted_skills: ["excel"] } }));
  assert.match(html, /Refuerza/);
  assert.match(html, /excel/);
  assert.doesNotMatch(html, /power query/);
});

test("demand filters preserve canonical aliases when finding resources in the educational library", async () => {
  const Library = await component("AdminLearningLibrary");
  const html = renderToStaticMarkup(createElement(Library, { focusSkill: "javascript", rows: [{ id: "js", title: "Fundamentos de programación", provider: "Ejemplo", skills: ["JS"], kind: "course", cost: "free", hours: 8 }, { id: "sql", title: "Consultas en bases de datos", provider: "Ejemplo", skills: ["sql"], kind: "course", cost: "free", hours: 8 }] }));
  assert.match(html, /Fundamentos de programación/);
  assert.doesNotMatch(html, /Consultas en bases de datos/);
});

test("company profile header uses age and identification only when returned by the sharing endpoint", async () => {
  const Hero = await component("CandidateHero");
  const html = renderToStaticMarkup(createElement(Hero, { candidate: { name: "Perfil de ejemplo", profession: "Ingeniera", availability: "immediate", birth_date: "1999-12-13", identification: { type: "CC", number: "EXAMPLE-1234" } } }));
  assert.match(html, /Edad/);
  assert.match(html, /Disponibilidad inmediata/);
  assert.match(html, /EXAMPLE-1234/);
  assert.doesNotMatch(html, /13\/12\/1999|Nacimiento/);
  const hidden = renderToStaticMarkup(createElement(Hero, { candidate: { name: "Perfil sin datos compartidos" } }));
  assert.doesNotMatch(hidden, /Edad|Nacimiento|Identificación|EXAMPLE-1234/);
});

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

test("professional summary reveals the local AI action only when editing the profile", async () => {
  const Panel = await component("ProfessionalSummary");
  const profile = { experience: "Mi texto personal", summary_mode: "custom" };
  const html = renderToStaticMarkup(createElement(Panel, { profile, editing: false, onChange: () => {}, onEdit: () => {} }));
  assert.ok(html.includes("Mi texto personal"));
  assert.ok(!html.includes("<textarea") && !html.includes("Generar con IA local") && !html.includes("Editar mi texto"));
  const editor = renderToStaticMarkup(createElement(Panel, { profile, editing: true, onChange: () => {}, onEdit: () => {} }));
  for (const value of ['maxLength="3000"', "Mi texto personal", "Guardar cambios", "Generar con IA local", 'aria-haspopup="dialog"']) assert.ok(editor.includes(value));
});

test("saved repository evidence exposes text editing without hiding its reference or skills", async () => {
  const Panel = await component("ProfileEvidence", "EvidenceCard");
  const html = renderToStaticMarkup(createElement(Panel, { row: { id: "project-1", title: "TalentSync AI", kind: "repository", description: "Desarrollé la plataforma.", url: "https://github.com/example/project", skills: ["python", "react"], analysis: { origin: "github_public", revision: "original-revision" } }, busy: false }));
  for (const value of ["Editar texto de TalentSync AI", 'aria-haspopup="dialog"', "Abrir referencia", "python", "react", "original-rev", "Retirar evidencia: TalentSync AI"]) assert.ok(html.includes(value), value);
});

test("evidence text editor starts with the complete saved text and offers save and cancel", async () => {
  const Panel = await component("EvidenceTextEditor");
  const html = renderToStaticMarkup(createElement(Panel, { row: { id: "project-1", title: "Taskflow", description: "Desarrollé la aplicación para organizar tareas.\nDiseñé su interfaz." }, onClose: () => {}, onSaved: () => {} }));
  for (const value of ["Editar texto de la evidencia", "Taskflow", "Desarrollé la aplicación", "Diseñé su interfaz", 'maxLength="2000"', "Guardar cambios", "Cancelar"]) assert.ok(html.includes(value), value);
  assert.ok(!html.includes('type="url"') && !html.includes("type=\"checkbox\""));
});

test("professional links expose common platforms in the editor and safe links in the saved profile", async () => {
  const Panel = await component("ProfileLinks");
  const value = [{ platform: "github", url: "https://github.com/my-projects", label: "" }];
  const html = renderToStaticMarkup(createElement(Panel, { value }));
  assert.ok(html.includes('href="https://github.com/my-projects"') && html.includes('rel="noopener noreferrer"') && html.includes("GitHub"));
  const editor = renderToStaticMarkup(createElement(Panel, { value, editing: true, onChange: () => {} }));
  for (const label of ["LinkedIn", "GitHub", "Behance", "GitLab", "Kaggle", "Portafolio personal", "Otro enlace", "Añadir enlace", "Eliminar enlace 1", "Guardar cambios"]) assert.ok(editor.includes(label), label);
  const unsafe = renderToStaticMarkup(createElement(Panel, { value: [{ platform: "other", url: "javascript:alert(1)" }] }));
  assert.ok(!unsafe.includes("href="));
});
