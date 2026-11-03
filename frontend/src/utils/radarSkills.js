import { skillName } from "./skillNames.js";

const fold = (value) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
export function browseRadarSkills(rows, query = "", page = 1, pageSize = 5) {
  const matches = [...rows].sort((a, b) => b.count - a.count || a.skill.localeCompare(b.skill, "es"))
    .filter((row) => fold(skillName(row.skill)).includes(fold(query.trim())));
  const pages = Math.max(1, Math.ceil(matches.length / pageSize));
  const current = Math.max(1, Math.min(page, pages));
  return { rows: matches.slice((current - 1) * pageSize, current * pageSize), total: matches.length, page: current, pages };
}
