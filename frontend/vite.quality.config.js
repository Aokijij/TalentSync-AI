import { defineConfig } from "vite";
import appConfig from "./vite.config.js";

export default defineConfig({ ...appConfig, build: { outDir: ".quality-dist", rollupOptions: { input: "quality/index.html" } } });
