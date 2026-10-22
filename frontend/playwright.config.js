import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./quality/specs", fullyParallel: true, forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0, workers: process.env.CI ? 2 : undefined,
  timeout: 30000, globalTimeout: 300000,
  reporter: [["list"], ["html", { open: "never" }]],
  use: { baseURL: "http://127.0.0.1:4175", browserName: "chromium", locale: "es-CO", timezoneId: "America/Bogota", reducedMotion: "reduce", trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: { command: "npm exec vite -- --host 127.0.0.1 --port 4175 --strictPort", url: "http://127.0.0.1:4175/quality/", reuseExistingServer: false, timeout: 30000 },
});
