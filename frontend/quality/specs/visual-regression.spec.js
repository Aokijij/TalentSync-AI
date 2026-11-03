import { test, expect } from "@playwright/test";
// Approved references use Windows and the Chromium revision pinned by Playwright.
// Linux keeps the functional suite; a dedicated Windows CI job compares pixels.
test.skip(process.env.TALENTSYNC_VISUAL_BASELINES !== "1", "Use npm run quality:visual for approved screenshots.");
for (const role of ["candidate", "company", "admin"]) for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Visual reference · ${role} · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 950 });
  await page.route("**/*", (route) => { const url = new URL(route.request().url()); return url.hostname === "127.0.0.1" && !url.pathname.startsWith("/api/") ? route.continue() : route.abort(); });
  await page.goto(`/quality/?system=1&role=${role}&theme=${theme}`);
  await page.evaluate(() => document.fonts.ready);
  const name = `${role}-${theme}-${width}`;
  await expect(page.locator('[data-quality="system"]')).toHaveScreenshot(`components-${name}.png`, { animations: "disabled" });
  await page.getByRole("button", { name: "Eliminar borrador de ejemplo" }).click();
  await expect(page.getByRole("alertdialog")).toHaveScreenshot(`confirmation-${name}.png`, { animations: "disabled" });
  await page.getByRole("alertdialog").getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.getByRole("button", { name: "Probar avisos" }).click();
  await expect(page.locator(".feedback-stack")).toHaveScreenshot(`notices-${name}.png`, { animations: "disabled" });
});
