export const skillLevels = { unspecified: "Sin indicar", learning: "En aprendizaje", basic: "Básico", intermediate: "Intermedio", advanced: "Avanzado", expert: "Experto" };
export function skillKey(value) {
  const key = String(value).trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  return ({ "node.js": "nodejs", springboot: "spring boot", microservices: "microservicios", postgres: "postgresql", k8s: "kubernetes", js: "javascript", ts: "typescript", "rest api": "api rest", "restful api": "api rest", "atencion al cliente": "servicio al cliente", "customer service": "servicio al cliente", dotnet: ".net", "gestion sst": "seguridad y salud en el trabajo", sst: "seguridad y salud en el trabajo" })[key] || key;
}
export const skillLevelFor = (levels, skill) => levels?.[skillKey(skill)] || "unspecified";
export function updateSkillLevel(levels, skill, level) { const next = { ...levels }; delete next[skillKey(skill)]; if (level !== "unspecified") next[skillKey(skill)] = level; return next; }

export function addProfileSkill(profile, input) {
  const value = input.trim(), key = skillKey(value);
  if (!value || profile.skills.some((item) => skillKey(item) === key)) return profile;
  return { ...profile, skills: [...profile.skills, value], skill_levels: { ...profile.skill_levels, [key]: profile.skill_levels?.[key] || "learning" } };
}
