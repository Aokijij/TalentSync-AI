import test from "node:test";
import assert from "node:assert/strict";
import { formatLearningHours } from "../src/utils/learningPresentation.js";

test("learning hours use at most one decimal without long floating-point tails", () => {
  assert.equal(formatLearningHours(2.0166666667), "2");
  assert.equal(formatLearningHours(2.1), "2.1");
  assert.equal(formatLearningHours(3.5), "3.5");
  assert.equal(formatLearningHours(0.833333), "0.8");
  assert.equal(formatLearningHours(0.01), "< 0.1");
  assert.equal(formatLearningHours(null), "Por confirmar");
});
