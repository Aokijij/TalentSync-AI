import assert from "node:assert/strict";
import test from "node:test";
import { TALENT_MINIMUM_OPTIONS, talentMinimum } from "../src/utils/talentMinimum.js";

test("talent filters migrate old saved thresholds and URLs to 40 through 100 in tens", () => {
  assert.deepEqual(TALENT_MINIMUM_OPTIONS, [40, 50, 60, 70, 80, 90, 100]);
  for (const value of [null, "", 0, -10, "bad", undefined]) assert.equal(talentMinimum(value), 40);
  assert.equal(talentMinimum(50), 50);
  assert.equal(talentMinimum("80"), 80);
  assert.equal(talentMinimum(61), 70);
  assert.equal(talentMinimum(87), 90);
  assert.equal(talentMinimum(140), 100);
});
