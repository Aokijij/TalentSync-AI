import { writeFile } from "node:fs/promises";

const DATASET =
  "https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=5000&$order=cod_dpto,cod_mpio";
const response = await fetch(DATASET);
if (!response.ok) throw new Error(`DIVIPOLA respondió ${response.status}`);

const rows = await response.json();
const locations = {};
for (const row of rows) {
  if (!row.dpto || !row.nom_mpio || row.tipo_municipio !== "Municipio") continue;
  const department = departmentName(row.dpto);
  const city = titleCase(row.nom_mpio).replace("Bogotá, D.c.", "Bogotá");
  (locations[department] ??= []).push(city);
}
for (const cities of Object.values(locations)) {
  cities.sort((a, b) => a.localeCompare(b, "es"));
}

const source = `// Generado desde DIVIPOLA (Datos Abiertos Colombia, dataset gdxc-w37w).\n` +
  `// No editar a mano: ejecuta npm run update:locations.\n` +
  `export const COLOMBIA_LOCATIONS = ${JSON.stringify(locations, null, 2)};\n\n` +
  `export const COLOMBIAN_DEPARTMENTS = Object.keys(COLOMBIA_LOCATIONS).sort(\n` +
  `  (a, b) => a.localeCompare(b, "es"),\n);\n\n` +
  `export function departmentForCity(city) {\n  return (\n` +
  `    COLOMBIAN_DEPARTMENTS.find((department) =>\n` +
  `      COLOMBIA_LOCATIONS[department].includes(city),\n` +
  `    ) || ""\n  );\n}\n`;

await writeFile(new URL("../src/constants/colombianCities.js", import.meta.url), source);
console.log(`Escritos ${rows.length} registros DIVIPOLA en ${Object.keys(locations).length} departamentos.`);

function titleCase(value) {
  return value
    .toLocaleLowerCase("es-CO")
    .replace(/(^|[\s'’-])\p{L}/gu, (letter) => letter.toLocaleUpperCase("es-CO"));
}

function departmentName(value) {
  const name = titleCase(value)
    .replace(/\s+(De|Del|Y)\s+/g, (match) => match.toLocaleLowerCase("es-CO"))
    .replace("Bogotá, D.c.", "Bogotá D.C.");
  if (name.startsWith("Archipiélago de San Andrés")) {
    return "San Andrés y Providencia";
  }
  return name;
}
