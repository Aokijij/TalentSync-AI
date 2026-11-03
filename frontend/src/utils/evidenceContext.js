const programmingSkills = new Set([
  "python", "javascript", "typescript", "java", "c", "c++", "c#", "csharp",
  "php", "ruby", "rust", "golang", "go", "kotlin", "swift", "scala", "sql",
  "html", "css", "html5", "css3", "react", "react.js", "reactjs", "angular",
  "vue", "vue.js", "node.js", "nodejs", "django", "fastapi", "spring boot",
  "git", "github", "programacion", "desarrollo web", "desarrollo de software",
]);

function normalize(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
}

// Presentation only: every candidate can open the optional integrations.
export function programmingEvidenceRelevant(profile, evidence = []) {
  if (evidence.some((row) => row.kind === "repository" || ["github_public", "codewars_public"].includes(row.analysis?.origin))) return true;
  if ((profile?.skills || []).some((skill) => programmingSkills.has(normalize(skill)))) return true;
  return /\b(desarrollador(?:a|es|as)?|programador(?:a|es|as)?|developer|software engineer|ingenier[oa] (?:de |en )?(?:sistemas|software|informatica)|desarrollo (?:de )?(?:software|web))\b/.test(normalize(profile?.profession));
}
