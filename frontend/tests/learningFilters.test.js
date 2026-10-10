import test from "node:test";
import assert from "node:assert/strict";
import { filterResources } from "../src/utils/learningFilters.js";

const resources = [
  { id: "local", title: "Conciliación", provider: "TalentSync", skills: ["finanzas"], kind: "project", cost: "free" },
  { id: "external", title: "Diseño accesible", provider: "Academia", skills: ["contraste"], kind: "course", cost: "paid", url: "https://example.com/course" },
  { id: "unknown", title: "Comunicación", provider: "Biblioteca", skills: [], kind: "workshop", cost: "unknown", url: "https://example.com/workshop" },
];
test("combines provider, cost, format and accent-insensitive search", () => {
  assert.deepEqual(filterResources(resources, { origin: "external", cost: "paid", kind: "course", query: "diseno" }).map((row) => row.id), ["external"]);
  assert.deepEqual(filterResources(resources, { origin: "local", cost: "free", query: "FINANZAS" }).map((row) => row.id), ["local"]);
  assert.deepEqual(filterResources(resources, { cost: "unknown" }).map((row) => row.id), ["unknown"]);
  assert.deepEqual(filterResources(resources, { origin: "local", cost: "paid" }), []);
});

test("provider, level and language filters compose without excluding legacy resources by default", () => {
  const catalog = [...resources, { id: "microsoft", title: "Datos", provider: "Microsoft Learn", skills: ["power bi"], kind: "course", cost: "free", url: "https://learn.microsoft.com/training", details: { level: "intermediate", languages: ["es", "en"] } }, { id: "google", title: "Data", provider: "Google", skills: ["sql"], kind: "course", cost: "paid", url: "https://grow.google", details: { level: "beginner", languages: ["en"] } }];
  assert.equal(filterResources(catalog).length, 5);
  assert.deepEqual(filterResources(catalog, { provider: "Microsoft Learn", cost: "free", language: "es", level: "intermediate" }).map((row) => row.id), ["microsoft"]);
  assert.deepEqual(filterResources(catalog, { provider: "Google", language: "es" }), []);
  assert.deepEqual(filterResources(catalog, { language: "en", level: "beginner", origin: "external" }).map((row) => row.id), ["google"]);
  assert.deepEqual(filterResources(catalog, { provider: "TalentSync" }).map((row) => row.id), ["local"]);
});
