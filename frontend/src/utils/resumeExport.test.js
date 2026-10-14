import assert from "node:assert/strict";
import { test } from "node:test";
import { resumeExportPayload } from "./resumeExport.js";

test("export carries only chosen sections and a draft, without modifying the profile or sending raw CV data", () => {
  const profile = { profession: "Diseñadora", skills: ["Figma"], resume_style: "classic", resume_color: "default", cv_text: "Private source", photo_filename: "private.png", preferences: { private_data: true } };
  const before = structuredClone(profile);
  const payload = resumeExportPayload(profile, "Persona", { sections: ["experiences"], style: "modern", color: "teal", includePhoto: false });
  assert.deepEqual(payload.sections, ["experiences"]);
  assert.equal(payload.include_photo, false);
  assert.equal(payload.profile.resume_style, "modern");
  assert.equal(payload.profile.resume_color, "teal");
  assert.equal(payload.profile.name, "Persona");
  for (const field of ["cv_text", "photo_filename", "preferences"]) assert.equal(payload.profile[field], undefined);
  assert.deepEqual(profile, before);
});
