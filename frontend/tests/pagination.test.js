import assert from "node:assert/strict";
import test from "node:test";

import { pageItems, totalPages } from "../src/utils/pagination.js";

test("paginates and clamps recommendation pages", () => {
  const items = Array.from({ length: 11 }, (_, index) => index + 1);
  assert.equal(totalPages(items, 5), 3);
  assert.deepEqual(pageItems(items, 2, 5), [6, 7, 8, 9, 10]);
  assert.deepEqual(pageItems(items, 99, 5), [11]);
});
