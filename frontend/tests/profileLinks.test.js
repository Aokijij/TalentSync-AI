import assert from "node:assert/strict";
import { test } from "node:test";
import { normalizeProfessionalUrl, profileLinksPayload } from "../src/utils/profileLinks.js";
import { resumeExportPayload } from "../src/utils/resumeExport.js";

test("profile links accept pasted domains and preserve a custom portfolio label", () => {
  assert.deepEqual(profileLinksPayload([{ platform: "github", url: " github.com/my-projects " }, { platform: "portfolio", url: "https://example.com/work", label: " Mi trabajo " }]), [{ platform: "github", url: "https://github.com/my-projects", label: "" }, { platform: "portfolio", url: "https://example.com/work", label: "Mi trabajo" }]);
  assert.equal(normalizeProfessionalUrl(""), "");
  assert.equal(normalizeProfessionalUrl("javascript:alert(1)"), "javascript:alert(1)");
  assert.deepEqual(profileLinksPayload([]), []);
});

test("profile links catch incomplete entries, unsafe protocols, credentials and misleading platform domains", () => {
  for (const row of [{ platform: "github", url: "" }, { platform: "other", url: "javascript:alert(1)" }, { platform: "other", url: "https://user:secret@example.com" }, { platform: "github", url: "https://github.com.example.com/user" }, { platform: "linkedin", url: "https://example.com" }]) assert.throws(() => profileLinksPayload([row]));
  assert.throws(() => profileLinksPayload([{ platform: "github", url: "github.com/user" }, { platform: "github", url: "https://github.com/user" }]), /No repitas/);
});

test("resume previews use the links in the current draft", () => {
  const links = [{ platform: "linkedin", url: "https://linkedin.com/in/me", label: "" }];
  const payload = resumeExportPayload({ links }, "Nombre", { sections: ["contact"], includePhoto: false, style: "modern", color: "blue" });
  assert.deepEqual(payload.profile.links, links);
});
