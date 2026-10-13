import assert from "node:assert/strict";
import test from "node:test";
import { isOngoing, selectCurrentEmployment } from "../src/utils/profileStatus.js";

test("selecting a current job clears other current markers without inventing end dates", () => {
  const rows = [{ start_date: "2020-02", is_current: true }, { start_year: "2018", end_year: "Presente" }, { role: "Nuevo", is_current: false }];
  const changed = selectCurrentEmployment(rows, 2, true);
  assert.equal(changed.filter(isOngoing).length, 1);
  assert.equal(changed[0].end_date, "");
  assert.equal(changed[1].end_year, "");
  assert.equal(changed[0].start_date, "2020-02");
  assert.equal(rows[0].is_current, true);
  assert.equal(selectCurrentEmployment(changed, 2, false).filter(isOngoing).length, 0);
  assert.equal(isOngoing({ is_current: true, end_year: "" }), true);
});
