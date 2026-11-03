import appQuality from "./playwright.config.js";
import { defineConfig } from "@playwright/test";

export default defineConfig({
  ...appQuality,
  testDir: "./quality/public-specs",
  outputDir: "./test-results-public",
  use: { ...appQuality.use, baseURL: "http://127.0.0.1:4186" },
  webServer: { command: "node node_modules/vite/bin/vite.js preview --config vite.public.config.js --host 127.0.0.1 --port 4186 --strictPort", url: "http://127.0.0.1:4186", reuseExistingServer: false },
});
