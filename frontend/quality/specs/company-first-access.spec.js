import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Company first access keeps decisions explicit · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1050 });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  await page.emulateMedia({ colorScheme: theme });
  let attempts = 0;
  await page.route("**/api/v1/auth/company/registration/complete", async (route) => {
    attempts++;
    const payload = route.request().postDataJSON();
    expect(payload.name).toBe("Equipo de ejemplo");
    expect(payload.confirmed).toBe(true);
    expect(payload.terms_accepted).toBe(true);
    expect(payload.data_processing_accepted).toBe(true);
    expect(payload).not.toHaveProperty("profession");
    await route.fulfill({ status: attempts === 1 ? 503 : 200, contentType: "application/json", body: JSON.stringify(attempts === 1 ? { detail: "Inténtalo de nuevo" } : { role: "company", registration_pending: false }) });
  });
  await page.goto(`/quality/?auth=complete&role=company&theme=${theme}`);
  await expect(page.getByRole("heading", { name: "Prepara tu acceso empresarial" })).toBeVisible();
  await expect(page.getByText("Correo de acceso confirmado", { exact: true })).toBeVisible();
  const checks = page.getByRole("checkbox");
  await expect(checks).toHaveCount(3);
  for (const check of await checks.all()) await expect(check).not.toBeChecked();
  await expect(page.getByText("Profesión", { exact: true })).toHaveCount(0);
  await page.locator(".social-registration-card").screenshot({ path: `../.local/demo-access-20261103/company-${theme}-${width}.png` });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  for (const check of await checks.all()) await check.check();
  await page.getByRole("button", { name: "Confirmar y continuar" }).click();
  await expect(page.getByRole("alert")).toContainText("Inténtalo de nuevo");
  expect(attempts).toBe(1);
  for (const check of await checks.all()) await expect(check).toBeChecked();
  await page.getByRole("button", { name: "Confirmar y continuar" }).click();
  await expect(page.getByText("Acceso empresarial preparado", { exact: true })).toBeVisible();
  expect(attempts).toBe(2);
});
