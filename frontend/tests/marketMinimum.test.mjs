import assert from "node:assert/strict";
import { test } from "node:test";
import { marketMinimum, meetsMarketMinimum } from "../src/utils/marketMinimum.js";
import { talentMinimum, TALENT_MINIMUM_OPTIONS } from "../src/utils/talentMinimum.js";

test("market browsing includes uncalculated and low matches; recommendations retain their 40% floor", () => {
  for (const value of [undefined, null, "", "0", "invalid", -1]) assert.equal(marketMinimum(value), 0);
  for (const score of [undefined, null, NaN, 0, 25, 39, 75]) assert.equal(meetsMarketMinimum(score, 0), true);
  for (const score of [undefined, null, NaN, 0, 39]) assert.equal(meetsMarketMinimum(score, 40), false);
  assert.equal(meetsMarketMinimum(40, 40), true);
  assert.equal(marketMinimum("60"), 60);
  assert.equal(talentMinimum(undefined), 40);
  assert.equal(TALENT_MINIMUM_OPTIONS.includes(0), false);
});
