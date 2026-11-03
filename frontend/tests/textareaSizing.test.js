import test from "node:test";
import assert from "node:assert/strict";
import { resizeTextarea } from "../src/utils/textareaSizing.js";

test("textarea sizing grows beyond its initial rows and shrinks after removing text", () => {
  const element = { style: {}, scrollHeight: 1400, offsetHeight: 82, clientHeight: 80, getClientRects: () => [{}] };
  resizeTextarea(element);
  assert.equal(element.style.height, "1402px");
  element.scrollHeight = 110;
  resizeTextarea(element);
  assert.equal(element.style.height, "112px");
});

test("a hidden textarea waits until its container becomes visible", () => {
  const element = { style: { height: "100px" }, getClientRects: () => [] };
  resizeTextarea(element);
  assert.equal(element.style.height, "100px");
});
