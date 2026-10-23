import { test, expect } from "@playwright/test";

for (const width of [360, 1280]) for (const theme of ["light", "dark"]) test(`Candidate social access and linking · ${width} · ${theme}`, async ({ page }) => {
  const errors = [], calls = [];
  let emailChanges = 0;
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width, height: 950 });
  await page.addInitScript((theme) => localStorage.setItem("talentsync_theme", theme), theme);
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request(), path = new URL(request.url()).pathname;
    calls.push({ path, method: request.method(), body: request.postDataJSON() });
    if (path === "/api/v1/account/social-identities") return route.fulfill({ json: [{ provider: "github" }] });
    if (path === "/api/v1/account/change-email") return ++emailChanges === 1 ? route.fulfill({ status: 503, json: { detail: "No fue posible solicitar el cambio." } }) : route.fulfill({ json: { message: "Revisa el enlace en tu nuevo correo." } });
    if (path === "/api/v1/account/social-identities/github" && request.method() === "DELETE") return route.fulfill({ json: { message: "Proveedor desvinculado." } });
    return route.fulfill({ status: 503, json: { detail: "Proveedor temporalmente no disponible. Inténtalo de nuevo." } });
  });
  await page.goto(`/quality/?auth=register&theme=${theme}`);
  for (const provider of ["Google", "GitHub"]) await expect(page.getByRole("button", { name: `Continuar con ${provider}`, exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: /LinkedIn/ })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Abrir bandeja de correo local" })).toHaveCount(0);
  await page.getByRole("button", { name: "Continuar con Google", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Proveedor temporalmente no disponible");
  await expect(page.getByRole("button", { name: "Continuar con GitHub", exact: true })).toBeEnabled();
  expect(calls.some((row) => row.path === "/api/v1/auth/social/google/start" && row.method === "POST")).toBe(true);
  await page.getByLabel("Nombre completo").fill("Persona de ejemplo");
  await page.getByLabel("Correo electrónico").fill("example@example.com");
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await expect(page.getByLabel("Profesión o cargo de interés")).toBeVisible();
  await expect(page.getByRole("group", { name: "Registro con proveedor" })).toHaveCount(0);
  await page.getByRole("button", { name: "Atrás", exact: true }).click();
  await page.screenshot({ path: `../.local/social-access/register-${theme}-${width}.png`, fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);

  await page.goto(`/quality/?auth=login&theme=${theme}`);
  await expect(page.getByRole("group", { name: "Acceso con proveedor" })).toBeVisible();
  await page.goto(`/quality/?auth=accounts&theme=${theme}`);
  await expect(page.getByRole("button", { name: /LinkedIn/ })).toHaveCount(0);
  const emailPanel = page.locator("#security-email");
  await expect(emailPanel.getByLabel("Nuevo correo")).toHaveCount(0);
  await emailPanel.getByRole("button", { name: "Cambiar correo" }).click();
  await emailPanel.getByLabel("Nuevo correo").fill("new@example.com");
  await emailPanel.getByLabel("Contraseña actual").fill("Synthetic-pass-2026!");
  await emailPanel.getByRole("button", { name: "Enviar enlace de confirmación" }).click();
  await expect(emailPanel.getByRole("alert")).toContainText("No fue posible");
  await expect(emailPanel.getByLabel("Nuevo correo")).toHaveValue("new@example.com");
  await expect(emailPanel.getByLabel("Contraseña actual")).toHaveValue("");
  await emailPanel.getByLabel("Contraseña actual").fill("Synthetic-pass-2026!");
  await emailPanel.getByRole("button", { name: "Enviar enlace de confirmación" }).click();
  await expect(emailPanel.getByRole("status")).toContainText("Revisa el enlace");
  await expect(emailPanel.getByText("person@example.com", { exact: true })).toBeVisible();
  await expect(emailPanel.getByLabel("Nuevo correo")).toHaveCount(0);
  await expect(page.getByText("Conectada", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Vincular Google", exact: true }).click();
  await page.getByLabel("Contraseña actual de TalentSync").fill("Synthetic-pass-2026!");
  await page.getByRole("button", { name: "Continuar al proveedor" }).click();
  await expect(page.getByRole("alert")).toContainText("Proveedor temporalmente no disponible");
  expect(calls.find((row) => row.path.endsWith("/google/link"))?.body).toEqual({ password: "Synthetic-pass-2026!", code: null });
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.screenshot({ path: `../.local/social-access/accounts-${theme}-${width}.png`, fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});

test("Unavailable providers and company registration preserve password access", async ({ page }) => {
  await page.route("**/api/v1/**", (route) => route.fulfill({ json: [] }));
  await page.goto("/quality/?auth=register&providers=off");
  await expect(page.getByLabel("Correo electrónico")).toBeVisible();
  await expect(page.getByRole("button", { name: /Continuar con/ })).toHaveCount(0);
  await page.goto("/quality/?auth=accounts&providers=off");
  for (const provider of ["Google", "GitHub"]) await expect(page.getByRole("button", { name: `Vincular ${provider}`, exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: /LinkedIn/ })).toHaveCount(0);
  await page.goto("/quality/?auth=register&role=company");
  await expect(page.getByLabel("Correo de tu cuenta empresarial")).toBeVisible();
  await expect(page.getByRole("button", { name: /Continuar con/ })).toHaveCount(0);
});

test("Social failure distinguishes the cause and offers a fresh provider attempt", async ({ page }) => {
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "Proveedor temporalmente no disponible." } }));
  await page.goto("/quality/?auth=error&reason=provider_unavailable");
  await expect(page.getByText("Referencia: GOOGLE · PROVIDER_UNAVAILABLE", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Continuar con Google", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Proveedor temporalmente no disponible");
  await page.goto("/quality/?auth=error&reason=provider_configuration");
  await expect(page.getByText(/ajuste de configuración/)).toBeVisible();
  await expect(page.getByRole("button", { name: /Continuar con/ })).toHaveCount(0);
});

test("Social registration redirects even when remembering the provider is blocked", async ({ page }) => {
  await page.addInitScript(() => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function (key, value) {
      if (key === "talentsync_last_method") throw new DOMException("Storage unavailable", "SecurityError");
      return original.call(this, key, value);
    };
  });
  await page.route("**/api/v1/auth/social/github/start", (route) => route.fulfill({ json: { url: "/quality/?auth=login&authorized=github" } }));
  await page.goto("/quality/?auth=register");
  await page.getByRole("button", { name: "Continuar con GitHub", exact: true }).click();
  await expect(page).toHaveURL(/authorized=github/);
});
