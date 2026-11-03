export const courseImportExample = [{ title: "Excel para preparar reportes", provider: "Nombre de la entidad", url: "https://formacion.example.org/curso-excel", instructions: "Aprende a organizar tablas, validar datos y construir un reporte con fórmulas y gráficos.", skills: ["excel", "analisis de datos"], hours: 12, category: "technology", kind: "course", cost: "free", active: false, details: { level: "beginner", languages: ["es"], certificate_cost: "unknown" } }];

export function previewCourseImport(text) {
  let rows;
  try { rows = JSON.parse(text); } catch { throw new Error("El formato no es válido. Usa el ejemplo: comillas dobles, corchetes al inicio y al final, y ninguna coma después del último campo."); }
  if (!Array.isArray(rows) || !rows.length || rows.length > 50) throw new Error("El archivo debe contener una lista de entre 1 y 50 cursos.");
  return rows.map((row, index) => {
    const fail = (message) => { throw new Error(`Curso ${index + 1}: ${message}`); };
    if (!row || typeof row !== "object" || Array.isArray(row)) fail("usa los campos del ejemplo.");
    for (const [field, label, minimum, maximum] of [["title", "nombre", 3, 160], ["provider", "entidad", 2, 120], ["instructions", "descripción", 10, 2000]]) if (typeof row[field] !== "string" || row[field].trim().length < minimum || row[field].length > maximum) fail(`el ${label} debe tener entre ${minimum} y ${maximum} caracteres.`);
    if (typeof row.url !== "string" || !/^https:\/\//.test(row.url)) fail("el enlace debe comenzar con https://.");
    if (!Array.isArray(row.skills) || !row.skills.length || row.skills.some((skill) => typeof skill !== "string" || !skill.trim())) fail("indica las habilidades como una lista de nombres entre comillas.");
    if (typeof row.hours !== "number" || !Number.isFinite(row.hours) || row.hours <= 0 || row.hours > 1000) fail("las horas deben ser un número mayor que 0 y hasta 1000, sin comillas.");
    for (const [field, values, label] of [
      ["category", ["general", "technology", "service", "sales", "administration", "finance", "logistics", "education", "design", "care"], "área"],
      ["kind", ["course", "workshop", "documentation"], "tipo"],
      ["cost", ["free", "paid", "unknown"], "coste"],
    ]) if (row[field] !== undefined && !values.includes(row[field])) fail(`el ${label} debe ser uno de estos valores: ${values.join(", ")}.`);
    if (row.details !== undefined && row.details !== null) {
      if (typeof row.details !== "object" || Array.isArray(row.details)) fail("details debe conservar la estructura del ejemplo.");
      if (row.details.level !== undefined && !["beginner", "intermediate", "advanced", "any"].includes(row.details.level)) fail("el nivel debe ser beginner, intermediate, advanced o any.");
    }
    return { ...row, active: false };
  });
}
