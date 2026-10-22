import test from "node:test";
import assert from "node:assert/strict";
import { filterResources } from "../src/utils/learningFilters.js";
import { courseAvailability } from "../src/utils/learningPresentation.js";

const resources = [
  { id: "local", title: "Conciliación", provider: "TalentSync", skills: ["finanzas"], kind: "project", cost: "free" },
  { id: "external", title: "Diseño accesible", provider: "Academia", skills: ["contraste"], kind: "course", cost: "paid", url: "https://example.com/course" },
  { id: "unknown", title: "Comunicación", provider: "Biblioteca", skills: [], kind: "workshop", cost: "unknown", url: "https://example.com/workshop" },
];
test("search ignores surrounding spaces and a whitespace-only search leaves the catalog visible", () => {
  assert.deepEqual(filterResources(resources, { query: "  conciliacion  " }).map((row) => row.id), ["local"]);
  assert.equal(filterResources(resources, { query: "   " }).length, resources.length);
});
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

test("public enrollment filters combine certificate cost and modality without implying a reserved seat", () => {
  const today = new Date().toISOString().slice(0, 10);
  const catalog = [
    { id: "sena", url: "https://betowa.sena.edu.co/", cost: "free", details: { certificate_cost: "conditional", languages: ["es"], enrollment: { status: "open", modality: "virtual", checked_on: today } } },
    { id: "closed", url: "https://example.com/", cost: "free", details: { certificate_cost: "free", enrollment: { status: "closed", modality: "hybrid", checked_on: today } } },
    { id: "legacy", cost: "free" },
  ];
  assert.deepEqual(filterResources(catalog, { cost: "free", language: "es", enrollment: "open", modality: "virtual", certificate: "conditional" }).map((row) => row.id), ["sena"]);
  assert.deepEqual(filterResources(catalog, { enrollment: "closed" }).map((row) => row.id), ["closed"]);
  assert.equal(filterResources(catalog).length, 3);
});

test("old or failed source observations never show an open enrollment as current", () => {
  const course = { details: { enrollment: { status: "open", checked_on: "2026-10-01" } } };
  assert.equal(courseAvailability(course, "2026-10-15").status, "open");
  assert.equal(courseAvailability(course, "2026-10-16").status, "unknown");
  assert.equal(courseAvailability({ ...course, availability: { status: "open", checked_on: "2026-10-01", unavailable: true } }, "2026-10-02").status, "unknown");
  assert.equal(courseAvailability({ availability: { status: "open", checked_on: "invalid" } }, "2026-10-02").status, "unknown");
});
