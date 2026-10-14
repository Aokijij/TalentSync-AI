import assert from "node:assert/strict";
import { test } from "node:test";
import { resumeFilename } from "../src/utils/resumeFilename.js";
test("every resume download names the candidate, platform and document without path or control characters", () => {
  assert.equal(resumeFilename("José Blanquicett"), "José Blanquicett - TalentSync - Hoja de vida.pdf");
  assert.equal(resumeFilename('José / Prueba\n:*?'), "José Prueba - TalentSync - Hoja de vida.pdf");
  assert.equal(resumeFilename(""), "Candidato - TalentSync - Hoja de vida.pdf");
});
