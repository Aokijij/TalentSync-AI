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
