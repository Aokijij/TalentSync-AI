import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
const output = await build({ entryPoints: [fileURLToPath(new URL("../src/components/ProfileCompletionRing.jsx", import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external" });
const module = { exports: {} };
new Function("require", "module", "exports", output.outputFiles[0].text)(require, module, module.exports);
const { ProfileCompletionRing, getProfileCompletion } = module.exports;

test("completion names the actual missing course and accommodates three-digit percentages", () => {
  const profile = { profession: "Diseñadora gráfica", phone: "3001234567", location: "Cali", department: "Valle", skills: ["a", "b", "c", "d", "e", "f"], experience: "Descripción profesional real. ".repeat(6), experiences: [1, 2].map(() => ({ role: "Diseñadora", company: "Equipo", start_date: "2020-01", description: "Diseño de materiales para diferentes canales. ".repeat(3) })), educations: [{ degree: "Diseño", institution: "Instituto", start_year: "2015" }], certifications: [], languages: [{ name: "Español", level: "NATIVE" }], availability: "immediate", preferred_modality: "remote", preferred_sector: "Diseño", desired_salary: 3000000, cv_filename: "cv.pdf", cv_text: "Texto" };
  assert.equal(getProfileCompletion(profile).percentage, 93);
  const partial = renderToStaticMarkup(createElement(ProfileCompletionRing, { profile, variant: "summary" }));
  assert.match(partial, /Te falta: curso o certificación/);
  profile.certifications = [{ name: "Diseño editorial", issuer: "Instituto" }];
  const complete = renderToStaticMarkup(createElement(ProfileCompletionRing, { profile, variant: "summary" }));
  assert.match(complete, /100%/);
  assert.match(complete, /is-complete/);
});
