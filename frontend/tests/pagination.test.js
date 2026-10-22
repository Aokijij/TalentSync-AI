import assert from "node:assert/strict";
import test from "node:test";

import { pageItems, pageNumber, paginationState, totalPages } from "../src/utils/pagination.js";

test("paginates and clamps recommendation pages", () => {
  const items = Array.from({ length: 11 }, (_, index) => index + 1);
  assert.equal(totalPages(items, 5), 3);
  assert.deepEqual(pageItems(items, 2, 5), [6, 7, 8, 9, 10]);
  assert.deepEqual(pageItems(items, 99, 5), [11]);
});

test("invalid URL pages, fractional pages and invalid sizes cannot produce empty or NaN ranges", () => {
  const items = Array.from({ length: 25 }, (_, index) => index);
  for (const value of ["abc", "Infinity", null, 0, -1]) {
    assert.equal(pageNumber(value), 1);
    assert.deepEqual(pageItems(items, value, 12), items.slice(0, 12));
  }
  assert.equal(pageNumber("2.9"), 2);
  for (const size of [0, -2, NaN, Infinity]) assert.equal(paginationState(25, 1, size).pageSize, 12);
});

test("shrinking or empty filtered lists retain a valid range and last page", () => {
  assert.deepEqual(paginationState(0, 9, 12), { page: 1, pages: 1, pageSize: 12, start: 0, end: 0, offset: 0, total: 0 });
  assert.deepEqual(paginationState(13, 9, 12), { page: 2, pages: 2, pageSize: 12, start: 13, end: 13, offset: 12, total: 13 });
  assert.deepEqual(pageItems([1, 2, 3], 20, 2), [3]);
});
