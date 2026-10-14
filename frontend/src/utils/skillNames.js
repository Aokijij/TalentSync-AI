const names = { sql: "SQL", python: "Python", excel: "Excel", git: "Git", "power bi": "Power BI", "api rest": "API REST", fastapi: "FastAPI", javascript: "JavaScript", typescript: "TypeScript", html: "HTML", html5: "HTML5", css: "CSS", css3: "CSS3", aws: "AWS", java: "Java", react: "React", nodejs: "Node.js" };
export const skillName = (value) => names[value.toLocaleLowerCase()] || value.charAt(0).toLocaleUpperCase() + value.slice(1);
export const skillKey = (value) => String(value || "").trim().normalize("NFKD").replace(/\p{Diacritic}/gu, "").toLowerCase();

export function pendingCvMentions(rows, skills, decisions) {
  const known = new Set(skills.map(skillKey));
  const resolved = Object.fromEntries(Object.entries(decisions).map(([key, value]) => [skillKey(key), value]));
  return [...new Map(rows.map((row) => [skillKey(row.skill), row])).values()].filter((row) => !known.has(skillKey(row.skill)) && !["confirmed", "dismissed"].includes(resolved[skillKey(row.skill)]));
}
