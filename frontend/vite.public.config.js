import { defineConfig, loadEnv } from "vite";
import appConfig from "./vite.config.js";
import { cpSync } from "node:fs";

const legalFields = ["NAME", "EMAIL", "CITY", "COUNTRY", "ADDRESS", "PHONE", "EFFECTIVE_DATE"];
export default defineConfig(({ mode }) => {
  const env = { ...loadEnv(mode, process.cwd(), ""), ...process.env };
  if (env.TALENTSYNC_PUBLIC_RELEASE === "1") {
    const missing = legalFields.filter((field) => !env[`VITE_LEGAL_${field}`]?.trim());
    if (missing.length) throw new Error(`Faltan datos públicos del responsable: ${missing.join(", ")}`);
    const date = env.VITE_LEGAL_EFFECTIVE_DATE;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(Date.parse(`${date}T00:00:00Z`))) throw new Error("Fecha legal inválida");
  }
  return {
    ...appConfig,
    plugins: [{
      name: "talentsync-informational-entry",
      transformIndexHtml: { order: "pre", handler: (html) => html.replace("/src/main.jsx", "/src/public-main.jsx").replace(/\s*<link rel="preconnect"[^>]*>/g, "") },
      generateBundle(_, bundle) {
        // This release must have no API dependency, secret, login or mailbox chunk.
        for (const asset of Object.values(bundle)) if (asset.type === "chunk" && /azurecontainerapps\.io|127\.0\.0\.1:8000|gmail\.send|LocalMailboxPage|AuthProvider/.test(asset.code)) throw new Error("La publicación informativa contiene código privado de la aplicación");
        this.emitFile({ type: "asset", fileName: "_headers", source: "/*\n  Content-Security-Policy: default-src 'self'; base-uri 'self'; connect-src 'self'; font-src 'self' data:; form-action 'none'; frame-ancestors 'none'; img-src 'self' data:; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()\n  Strict-Transport-Security: max-age=31536000\n" });
        this.emitFile({ type: "asset", fileName: "_redirects", source: "/* /index.html 200\n" });
      },
      writeBundle() { cpSync(new URL("./public/brand", import.meta.url), new URL("./public-dist/brand", import.meta.url), { recursive: true }); },
    }, ...appConfig.plugins],
    // Prevent the application's Azure headers being copied into this release.
    publicDir: false,
    build: { outDir: "public-dist" },
  };
});
