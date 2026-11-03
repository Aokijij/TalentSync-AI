import { test, expect } from "@playwright/test";

async function open(page, path, theme = "light") {
  await page.goto(`/quality/?entry=1&theme=${theme}&path=${encodeURIComponent(path)}`);
}

async function fits(page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
}

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Email recovery and confirmation · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 950 });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  const errors = [], calls = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let unavailable = true, expired = true;
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request(), path = new URL(request.url()).pathname;
    calls.push({ path, method: request.method(), body: request.postDataJSON() });
    if (path.endsWith("/auth/password/request")) return unavailable
      ? route.fulfill({ status: 503, json: { detail: "El servicio de correo no está configurado" } })
      : route.fulfill({ json: { message: "Si la cuenta corresponde, encontrarás las instrucciones en su correo." } });
    if (path.endsWith("/auth/action/confirm")) return expired
      ? route.fulfill({ status: 400, json: { detail: "El enlace venció o ya fue utilizado" } })
      : route.fulfill({ json: { message: "Cambio confirmado. Puedes continuar o iniciar sesión de nuevo." } });
    return route.fulfill({ status: 404, json: { detail: "Ruta inesperada" } });
  });

  await open(page, "/recuperar-acceso?portal=company", theme);
  await expect(page.getByRole("heading", { name: "Recupera tu acceso", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Volver al inicio de sesión", exact: true })).toHaveAttribute("href", "/empresa/login");
  await expect(page.locator('a[href="/desarrollo/correos"]')).toHaveCount(0);
  await page.getByLabel("Correo electrónico", { exact: true }).fill("authorized@example.com");
  await page.getByRole("button", { name: "Enviar enlace de recuperación", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(1);
  await expect(page.getByRole("alert")).toContainText("servicio de correo");
  await expect(page.getByRole("heading", { name: "Revisa tu correo", exact: true })).toHaveCount(0);
  unavailable = false;
  await page.getByRole("button", { name: "Enviar enlace de recuperación", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Revisa tu correo", exact: true })).toBeVisible();
  await expect(page.locator(".account-mail-card").getByRole("status")).toHaveCount(1);
  await expect(page.locator(".account-mail-card").getByRole("status")).toContainText("authorized@example.com");
  await expect(page.locator(".account-mail-card").getByRole("status")).toContainText("Spam");
  await expect(page.locator(".feedback-toast")).toHaveCount(0);
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
  await fits(page);
  await page.screenshot({ path: `../.local/production-mail/recovery-${theme}-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: "Revisar dirección o volver a solicitar", exact: true }).click();
  await expect(page.getByLabel("Correo electrónico", { exact: true })).toHaveValue("authorized@example.com");

  await open(page, "/cuenta/confirmar?purpose=reset&token=synthetic-email-review", theme);
  const count = calls.filter((row) => row.path.endsWith("/action/confirm")).length;
  await page.getByLabel("Nueva contraseña", { exact: true }).fill("Synthetic-password-2026!");
  await page.getByLabel("Repite la nueva contraseña", { exact: true }).fill("Different-password-2026!");
  await page.getByRole("button", { name: "Guardar nueva contraseña", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("no coinciden");
  expect(calls.filter((row) => row.path.endsWith("/action/confirm"))).toHaveLength(count);
  await page.getByLabel("Nueva contraseña", { exact: true }).fill("á".repeat(40));
  await page.getByLabel("Repite la nueva contraseña", { exact: true }).fill("á".repeat(40));
  await page.getByRole("button", { name: "Guardar nueva contraseña", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("72 bytes");
  expect(calls.filter((row) => row.path.endsWith("/action/confirm"))).toHaveLength(count);
  await page.getByLabel("Nueva contraseña", { exact: true }).fill("Synthetic-password-2026!");
  await page.getByLabel("Repite la nueva contraseña", { exact: true }).fill("Synthetic-password-2026!");
  await page.getByRole("button", { name: "Mostrar contraseña", exact: true }).click();
  await expect(page.getByLabel("Nueva contraseña", { exact: true })).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Ocultar contraseña", exact: true }).click();
  await page.getByRole("button", { name: "Guardar nueva contraseña", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("venció");
  await expect(page.getByRole("link", { name: "Solicitar un nuevo enlace", exact: true })).toHaveAttribute("href", "/recuperar-acceso");
  await fits(page);
  await page.screenshot({ path: `../.local/production-mail/reset-${theme}-${width}.png`, fullPage: true });
  expired = false;
  await page.getByRole("button", { name: "Guardar nueva contraseña", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Tu contraseña se actualizó", exact: true })).toBeVisible();

  for (const [purpose, button, title] of [["verify", "Confirmar mi correo", "Tu correo está confirmado"], ["email", "Confirmar nuevo correo", "Tu correo se actualizó"]]) {
    await open(page, `/cuenta/confirmar?purpose=${purpose}&token=synthetic-email-review`, theme);
    await expect(page.getByRole("button", { name: button, exact: true })).toBeVisible();
    await page.getByRole("button", { name: button, exact: true }).click();
    await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
    await fits(page);
    await page.screenshot({ path: `../.local/production-mail/confirmed-${purpose}-${theme}-${width}.png`, fullPage: true });
  }
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await fits(page);
  expect(errors).toEqual([]);
});

test("Incomplete and unknown account links never submit a change", async ({ page }) => {
  const calls = [];
  await page.route("**/api/v1/**", (route) => { calls.push(route.request().method()); return route.fulfill({ json: {} }); });
  for (const path of ["/cuenta/confirmar", "/cuenta/confirmar?purpose=reset", "/cuenta/confirmar?purpose=toString&token=synthetic"]) {
    await open(page, path);
    await expect(page.getByRole("heading", { name: "Revisa tu enlace", exact: true })).toBeVisible();
    await expect(page.locator("form")).toHaveCount(0);
  }
  expect(calls).toEqual([]);
});

test("Production security hides development mailbox even with an incorrect server flag", async ({ page }) => {
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    return route.fulfill({ json: path.endsWith("/social-identities") ? [] : {} });
  });
  // This fixture deliberately passes localMail=true; quality builds use production mode.
  await page.goto("/quality/?auth=accounts");
  await expect(page.getByRole("heading", { name: "Correo electrónico", exact: true })).toBeVisible();
  await expect(page.locator('a[href="/desarrollo/correos"]')).toHaveCount(0);
  await expect(page.getByText("Herramientas de desarrollo", { exact: true })).toHaveCount(0);
});

for (const theme of ["light", "dark"]) test(`Pending email confirmation keeps its state until the link is confirmed · ${theme}`, async ({ page }) => {
  await page.setViewportSize({ width: theme === "dark" ? 360 : 1280, height: 950 });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  let available = false;
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/account/verify-email")) return available
      ? route.fulfill({ json: { message: "Si la cuenta corresponde, encontrarás las instrucciones en su correo." } })
      : route.fulfill({ status: 503, json: { detail: "El servicio de correo no está configurado" } });
    if (path.endsWith("/account/privacy")) return route.fulfill({ json: {} });
    return route.fulfill({ json: [] });
  });
  await page.goto("/quality/?entry=1&signed=candidate&email=pending&path=%2Fseguridad");
  const panel = page.locator("#security-email");
  await panel.getByRole("button", { name: "Enviar confirmación", exact: true }).click();
  await expect(panel.getByRole("alert")).toContainText("servicio de correo");
  await expect(panel.getByRole("status")).toHaveCount(0);
  available = true;
  await panel.getByRole("button", { name: "Enviar confirmación", exact: true }).click();
  await expect(panel.getByRole("status")).toContainText("Destino: person@example.com");
  await expect(panel.getByRole("status")).toContainText("30 minutos");
  await expect(panel.getByText("Pendiente de confirmar", { exact: true })).toBeVisible();
  await expect(panel.locator('a[href="/desarrollo/correos"]')).toHaveCount(0);
  await expect(page.locator(".feedback-toast")).toHaveCount(0);
  await fits(page);
  await page.screenshot({ path: `../.local/production-mail/pending-email-${theme}.png`, fullPage: true });
});
