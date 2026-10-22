import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";

const cases = [["JobsPage", "candidate"], ["LearningPage", "candidate"], ["ApplicationsPage", "candidate"], ["ProfilePage", "candidate"], ["CandidateDashboard", "candidate"], ["CompanyApplicationsPage", "company"], ["CompanyTalentPage", "company"], ["CompanyJobsPage", "company"], ["CompanyDashboard", "company"], ["AdminManagementPage", "admin"], ["AdminDashboard", "admin"], ["NotificationsPage", "candidate"]];
const compiled = await build({ stdin: { contents: cases.map(([name]) => `export { ${name} } from './pages/${name}.jsx';`).join("\n"), resolveDir: fileURLToPath(new URL("../src", import.meta.url)), loader: "jsx" }, bundle: true, write: false, platform: "node", format: "cjs", packages: "external", jsx: "automatic", loader: { ".css": "empty" }, plugins: [{ name: "isolated-page-accounts", setup(builder) {
  builder.onResolve({ filter: /hooks\/useAuth\.js$/ }, () => ({ path: "auth", namespace: "fixture" }));
  builder.onResolve({ filter: /contexts\/FeedbackContext\.jsx$/ }, () => ({ path: "feedback", namespace: "fixture" }));
  builder.onResolve({ filter: /(?:api\/client|^\.\/client)\.js$/ }, () => ({ path: "api", namespace: "fixture" }));
  builder.onLoad({ filter: /.*/, namespace: "fixture" }, ({ path }) => ({ loader: "js", contents: path === "auth" ? "export const useAuth=()=>({user:{id:1,role:globalThis.__talentAuditRole,name:'Persona de ejemplo',email:'example@example.com'},accessOptions:{},updateUser(){}});" : path === "feedback" ? "export const useFeedback=()=>({confirm:async()=>false,notify(){}});" : "export const api={}; export const cancelPendingRequests=()=>{}; export const apiFileUrl=value=>value; export const getApiErrorMessage=()=>'';" }));
} }] });
const module = { exports: {} };
const storage = { getItem: () => null };
globalThis.localStorage = storage;
globalThis.window = { location: { search: "?filters=1&match=0&page=invalid" }, sessionStorage: storage, addEventListener() {}, removeEventListener() {} };
new Function("require", "module", "exports", compiled.outputFiles[0].text)(createRequire(import.meta.url), module, module.exports);

for (const [name, role] of cases) test(`${name} renders its initial state without browser, real credentials or undefined references`, () => {
  globalThis.__talentAuditRole = role;
  const html = renderToStaticMarkup(createElement(MemoryRouter, { initialEntries: ["/vacantes?filters=1&match=0&page=invalid"] }, createElement(module.exports[name])));
  assert.ok(html.length > 10);
  assert.doesNotMatch(html, /\bNaN\b|Invalid Date/);
  if (name === "AdminManagementPage") assert.match(html, /Cargando registros…/);
  if (name === "JobsPage") {
    assert.match(html, /<option value="40" selected="">40%<\/option>/);
    assert.doesNotMatch(html, /<option value="0">0%<\/option>/);
  }
});
