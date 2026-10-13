import test from "node:test";
import assert from "node:assert/strict";
import { monthChoice } from "../src/utils/monthChoice.js";

test("the month calendar prevents future dates and endings before employment starts", () => {
  assert.equal(monthChoice("2026", 9, "2024-05", "2026-10").disabled, false);
  assert.equal(monthChoice("2026", 10, "2024-05", "2026-10").disabled, true);
  assert.equal(monthChoice("2024", 3, "2024-05", "2026-10").disabled, true);
  assert.deepEqual(monthChoice("2024", 4, "2024-05", "2026-10"), { value: "2024-05", disabled: false });
  assert.equal(monthChoice("202", 4, "1900-01", "2026-10").disabled, true);
});
