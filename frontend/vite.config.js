import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import { existsSync, readFileSync } from "node:fs";

// Only these authorized public contact fields may enter a browser bundle.
const legalFile = new URL("../.local/public-legal.json", import.meta.url);
const legalIdentity = existsSync(legalFile) ? JSON.parse(readFileSync(legalFile, "utf8")) : {};
const legalFields = ["NAME", "EMAIL", "CITY", "COUNTRY", "ADDRESS", "PHONE", "EFFECTIVE_DATE"];
const legalDefinitions = Object.fromEntries(legalFields.filter((field) => !process.env[`VITE_LEGAL_${field}`] && typeof legalIdentity[field] === "string").map((field) => [`import.meta.env.VITE_LEGAL_${field}`, JSON.stringify(legalIdentity[field])]));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: legalDefinitions,
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
});
