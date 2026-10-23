import { defineConfig } from "@playwright/test";
import { existsSync, readFileSync } from "node:fs";

const visualBaselines = process.env.TALENTSYNC_VISUAL_BASELINES === "1";
const localBrowserFile = new URL("../.local/playwright-browser.json", import.meta.url);
let executablePath = visualBaselines ? undefined : process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
if (!visualBaselines && !executablePath && existsSync(localBrowserFile)) executablePath = JSON.parse(readFileSync(localBrowserFile, "utf8")).executablePath;
if (executablePath && !existsSync(executablePath)) throw new Error("No existe el navegador configurado para Playwright. Revisa PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH o .local/playwright-browser.json.");

export default defineConfig({
  testDir: "./quality/specs", fullyParallel: true, forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0, workers: 2,
  snapshotPathTemplate: "{testDir}/../baselines/{platform}/{arg}{ext}",
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.001, threshold: 0.15, animations: "disabled" } },
  timeout: 45000, globalTimeout: 300000,
  reporter: [["list"], ["html", { open: "never" }]],
  use: { baseURL: "http://127.0.0.1:4175", browserName: "chromium", launchOptions: executablePath ? { executablePath } : undefined, locale: "es-CO", timezoneId: "America/Bogota", reducedMotion: "reduce", trace: "retain-on-failure", screenshot: "only-on-failure" },
  webServer: { command: "node quality/server.mjs", url: "http://127.0.0.1:4175/quality/", reuseExistingServer: false, timeout: 60000 },
});
