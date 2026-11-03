import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`External catalogue and YouTube controls · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 950 });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(`/quality/?externalSources=1&role=admin&theme=${theme}`);
  await expect(page.locator(".external-catalog-metrics")).toContainText("129");
  await expect(page.locator(".external-catalog-metrics")).toContainText("Disponibles");
  await expect(page.getByRole("heading", { name: "Convierte una lista en una ruta de estudio" })).toBeVisible();
  await expect(page.getByLabel("Enlace o identificador de la lista")).toBeVisible();
  await page.getByRole("button", { name: "Actualizar catálogo", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sincronizando en segundo plano" })).toBeDisabled();
  await page.getByRole("button", { name: "Actualizar estado", exact: true }).click();
  await expect(page.getByRole("button", { name: "Actualizar catálogo", exact: true })).toBeEnabled();
  await expect(page.locator(".brand-symbol")).toHaveCount(1);
  await page.screenshot({ path: `../.local/release-20261103/catalog-youtube-${theme}-${width}.png`, fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  const layout = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth, nodes: [...document.querySelectorAll("body *")].filter((node) => node.getBoundingClientRect().right > innerWidth + 1).map((node) => String(node.className)).slice(0, 15) }));
  expect(layout.overflow, JSON.stringify(layout.nodes)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});
