export const challengeLevels = { beginner: "Básico", intermediate: "Intermedio", advanced: "Avanzado", fundamentals: "Fundamentos" };
export const levelOrder = { beginner: 0, fundamentals: 0, intermediate: 1, advanced: 2 };
export const searchText = (value) => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
export function filterChallenges(rows, { query = "", level = "", status = "", onlyPlan = false } = {}, planIds = new Set()) {
  return rows.filter((row) => (!level || row.level === level) && (!onlyPlan || planIds.has(row.id)) && (!status || (status === "passed" ? row.last_attempt?.passed : status === "pending" ? !row.last_attempt?.passed : row.last_attempt?.status === "active")) && searchText([row.title, row.skill, row.context, ...(row.topics || [])].join(" ")).includes(searchText(query.trim())));
}
