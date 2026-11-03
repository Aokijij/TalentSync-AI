import assert from "node:assert/strict";
import test from "node:test";
import { citySuggestions } from "../src/utils/citySuggestions.js";

test("city suggestions prioritize frequent cities and match accents without accepting unknown names", () => {
  const options = ["Abejorral, Antioquia", "Medellín, Antioquia", "Bogotá, Bogotá D.C.", "San José De Cúcuta, Norte de Santander", "Santiago De Cali, Valle del Cauca"];
  assert.deepEqual(citySuggestions(options, "").slice(0, 3), ["Bogotá, Bogotá D.C.", "Medellín, Antioquia", "Santiago De Cali, Valle del Cauca"]);
  assert.deepEqual(citySuggestions(options, "medellin"), ["Medellín, Antioquia"]);
  assert.deepEqual(citySuggestions(options, "cucuta"), ["San José De Cúcuta, Norte de Santander"]);
  assert.deepEqual(citySuggestions(options, "Ciudad inventada"), []);
});
