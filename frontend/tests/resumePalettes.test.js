import assert from "node:assert/strict";
import test from "node:test";
import { getResumePalette, getResumePalettes } from "../src/constants/resumePalettes.js";

test("each style has four named palettes and preserves its default design", () => {
  for (const style of ["classic", "modern", "minimal"]) {
    assert.equal(getResumePalettes(style).length, 4);
    assert.equal(getResumePalette(style).id, "default");
  }
  assert.equal(getResumePalette("modern").label, "Violeta");
});

test("switching styles falls back when a color is not available", () => {
  assert.equal(getResumePalette("classic", "teal").id, "default");
  assert.equal(getResumePalette("minimal", "forest").id, "forest");
  assert.equal(getResumePalette("unknown", "unknown").id, "default");
});

test("palettes provide fixed print-safe colors rather than app theme colors", () => {
  for (const style of ["classic", "modern", "minimal"]) {
    for (const palette of getResumePalettes(style)) {
      for (const color of Object.values(palette.variables)) assert.match(color, /^#[0-9a-f]{6}$/i);
    }
  }
});
