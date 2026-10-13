import test from "node:test";
import assert from "node:assert/strict";
import { experiencePeriod } from "../src/utils/experienceDates.js";

test("month dates display in Spanish and current jobs have an explicit ending", () => {
  const period = experiencePeriod({ start_date: "2024-01", end_date: "2024-12" });
  assert.match(period, /2024/);
  assert.match(period, /ene/);
  assert.match(experiencePeriod({ start_date: "2024-01", is_current: true }), /Actualidad$/);
  assert.equal(experiencePeriod({ start_year: "2020", end_year: "2023" }), "2020 — 2023");
  assert.match(experiencePeriod({ start_date: "2024-01" }), /Sin fecha$/);
});
