import { mkdir, readFile, writeFile } from "node:fs/promises";
import { renderPublicPage } from "../frontend/.public-render/public-prerender.js";

const fullApp = process.argv.includes("--full-app");
const output = new URL(fullApp ? "../frontend/dist/" : "../frontend/public-dist/", import.meta.url);
const template = await readFile(new URL("index.html", output), "utf8");
// Lazy route CSS is needed for readable public and legal pages before JavaScript loads.
let publicStyles = "";
if (fullApp) {
  const manifest = JSON.parse(await readFile(new URL(".vite/manifest.json", output), "utf8"));
  const styles = new Set();
  const seen = new Set();
  function collect(key) {
    if (seen.has(key)) return;
    seen.add(key);
    const entry = manifest[key];
    if (!entry) return;
    for (const css of entry.css || []) styles.add(css);
    for (const dependency of entry.imports || []) collect(dependency);
  }
  for (const [key, entry] of Object.entries(manifest)) {
    if (entry.isEntry || /(?:LandingPage|LegalPage)/.test(key)) collect(key);
  }
  publicStyles = [...styles].filter((css) => !template.includes(`/${css}`)).map((css) => `<link rel="stylesheet" href="/${css}" />`).join("");
}
const routes = [
  ["/", "TalentSync", "Oportunidades con contexto, tu CV y formación por habilidades. Conoce TalentSync para candidatos."],
  ["/candidatos", "TalentSync", "Prepara tu postulación, organiza tu formación y sigue tus procesos y entrevistas con TalentSync."],
  ["/empresas", "TalentSync", "Publica ofertas claras, revisa candidaturas y coordina entrevistas y decisiones en TalentSync."],
  ["/privacidad", "Privacidad y tratamiento de datos · TalentSync", "Conoce al responsable de TalentSync, los usos de tus datos, las integraciones de Google y cómo ejercer tus derechos."],
  ["/terminos", "Términos de uso · TalentSync", "Consulta las condiciones de uso de TalentSync y el alcance de las ofertas, recomendaciones, cursos y procesos de selección."],
];
for (const [path, title, description] of routes) {
  const directory = new URL(path === "/" ? "./" : `${path.slice(1)}/`, output);
  await mkdir(directory, { recursive: true });
  const html = template.replace('<div id="root"></div>', `<div id="root">${renderPublicPage(path, !fullApp)}</div>`)
    .replace(/<title>.*?<\/title>/, `<title>${title}</title>`)
    .replace(/(<meta\s+name="description"\s+content=")[^"]*("\s*\/?>)/, `$1${description}$2`)
    .replace("</head>", `${publicStyles}<link rel="canonical" href="https://talentsync-ai.pages.dev${path}" /></head>`);
  await writeFile(new URL("index.html", directory), html);
}
await writeFile(new URL("robots.txt", output), "User-agent: *\nAllow: /\nSitemap: https://talentsync-ai.pages.dev/sitemap.xml\n");
await writeFile(new URL("sitemap.xml", output), `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${routes.map(([path]) => `<url><loc>https://talentsync-ai.pages.dev${path}</loc></url>`).join("")}</urlset>`);
console.log("Landings de candidatos y empresas, privacidad y términos generados como HTML legible sin JavaScript.");
