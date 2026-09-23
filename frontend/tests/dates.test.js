import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { formatRelativeTime, isWithinDays } from "../src/utils/dates.js";

describe("vacancy dates", () => {
  const now = new Date("2026-09-22T12:00:00Z");

  it("formats recent vacancies in natural Spanish", () => {
    assert.equal(formatRelativeTime("2026-09-22T11:40:00Z", now), "Hace 20 min");
    assert.equal(formatRelativeTime("2026-09-20T12:00:00Z", now), "Hace 2 días");
    assert.equal(formatRelativeTime("2026-09-15T12:00:00Z", now), "Hace 1 semana");
  });

  it("filters by publication age", () => {
    assert.equal(isWithinDays("2026-09-20T12:00:00Z", 7, now), true);
    assert.equal(isWithinDays("2026-08-20T12:00:00Z", 30, now), false);
  });
});
