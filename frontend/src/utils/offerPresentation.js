import { skillKey } from "./skillLevels.js";

export function detectedRequirements(data, existing = []) {
  const seen = new Set(existing.map((row) => skillKey(row.skill)));
  return (data.requirements || (data.skills || []).map((skill) => ({ skill }))).flatMap((row) => {
    const key = skillKey(row.skill);
    if (!key || seen.has(key)) return [];
    seen.add(key);
    return [{ skill: row.skill, essential: row.essential === true, level: ["basic", "intermediate", "advanced", "expert"].includes(row.level) ? row.level : "basic", weight: 1 }];
  });
}

export function publicationLabel(status, canPublish) {
  return ({ active: "Publicada", paused: "Pausada", closed: "Cerrada", filled: "Cubierta" })[status] || (canPublish ? "Lista para publicar" : "Revisa los datos pendientes");
}

export function qualityColor(summary) {
  const score = summary?.score || 0;
  const code = summary?.rating?.code || (score >= 90 ? "A" : score >= 75 ? "B" : score >= 50 ? "C" : "D");
  return ({ A: "is-complete", B: "is-ready", C: "is-pending", D: "is-initial" })[code] || "is-pending";
}
