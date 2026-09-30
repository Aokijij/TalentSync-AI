import assert from "node:assert/strict";
import test from "node:test";

import { currencyDigits, formatCurrencyInput } from "../src/utils/currency.js";

test("formats Colombian salary inputs while preserving their numeric value", () => {
  assert.equal(formatCurrencyInput(4500000), "4.500.000");
  assert.equal(currencyDigits("$ 4.500.000 COP"), 4500000);
  assert.equal(currencyDigits(""), null);
});
