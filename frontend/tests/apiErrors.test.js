import test from "node:test";
import assert from "node:assert/strict";
import { validationMessage } from "../src/api/errors.js";

test("validation errors use Spanish and identify the vacancy field", () => {
  assert.equal(validationMessage({ type: "string_too_short", loc: ["body", "description"], ctx: { min_length: 10 }, msg: "String should have at least 10 characters" }), "Descripción: escribe al menos 10 caracteres");
  assert.equal(validationMessage({ type: "missing", loc: ["body", "title"] }), "Cargo: completa este campo");
  assert.equal(validationMessage({ type: "value_error", loc: ["body", "languages", 0, "level"], msg: "Value error, Elige un nivel válido" }), "Idiomas: Elige un nivel válido");
});
