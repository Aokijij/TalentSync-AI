import assert from "node:assert/strict";
import test from "node:test";
import { TALENT_MINIMUM_OPTIONS, talentMinimum } from "../src/utils/talentMinimum.js";

test("talent filters migrate old saved thresholds and URLs to 60 through 100 in tens", () => {
  assert.deepEqual(TALENT_MINIMUM_OPTIONS, [60, 70, 80, 90, 100]);
  for (const value of [null, "", 0, -10, 50, "bad", undefined]) assert.equal(talentMinimum(value), 60);
  assert.equal(talentMinimum("80"), 80);
  assert.equal(talentMinimum(61), 70);
  assert.equal(talentMinimum(87), 90);
  assert.equal(talentMinimum(140), 100);
});
