import assert from "node:assert/strict";
import test from "node:test";

import {
  COLOMBIA_LOCATIONS,
  COLOMBIAN_DEPARTMENTS,
  departmentForCity,
} from "../src/constants/colombianCities.js";

test("includes the complete official municipality catalog", () => {
  assert.equal(COLOMBIAN_DEPARTMENTS.length, 33);
  assert.ok(Object.values(COLOMBIA_LOCATIONS).flat().length >= 1100);
  assert.equal(COLOMBIA_LOCATIONS.Antioquia.length, 125);
  assert.ok(COLOMBIA_LOCATIONS.Antioquia.includes("Yondó"));
  assert.equal(departmentForCity("Medellín"), "Antioquia");
});
