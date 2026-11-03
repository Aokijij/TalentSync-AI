import { test, expect } from "@playwright/test";

async function setup(page, role, theme, width) {
  await page.setViewportSize({ width, height: 950 });
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/notifications/unread-count")) return route.fulfill({ json: { count: 0 } });
    if (path.endsWith("/organization/access") || path.endsWith("/organization/me")) return route.fulfill({ json: { active: true, role: "owner", name: "Organización de revisión", verification_status: "verified" } });
    return route.fulfill({ status: 404, json: { detail: "Ruta no prevista en esta revisión" } });
  });
  await page.goto(`/quality/?design=1&role=${role}&theme=${theme}`);
}

for (const role of ["candidate", "company", "admin"]) for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Shared design and keyboard access · ${role} · ${theme} · ${width}`, async ({ page }) => {
  const errors = []; page.on("pageerror", (error) => errors.push(error.message));
  await setup(page, role, theme, width);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Saltar al contenido", exact: true })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
  const primary = page.locator(".design-primary"), danger = page.locator(".design-danger");
  for (const action of [primary, danger]) {
    expect(await contrast(action)).toBeGreaterThanOrEqual(4.5);
    await action.hover();
    expect(await contrast(action)).toBeGreaterThanOrEqual(4.5);
  }
  const description = page.getByRole("textbox", { name: "Descripción", exact: true });
  expect(await contrast(description, "placeholder")).toBeGreaterThanOrEqual(4.5);
  expect(await contrast(description, "border")).toBeGreaterThanOrEqual(3);
  await expect(page.getByRole("textbox", { name: "Dato requerido", exact: true })).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByText("Esta explicación permanece visible si hay un error.", { exact: true })).toBeVisible();
  await description.fill("Información aún sin guardar");
  const first = page.getByRole("tab", { name: "Resumen", exact: true });
  await first.focus(); await page.keyboard.press("ArrowRight");
  await expect(page.getByRole("tab", { name: "Vista previa", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Home");
  await expect(first).toHaveAttribute("aria-selected", "true");
  await expect(description).toHaveValue("Información aún sin guardar");
  await page.evaluate(() => {
    document.activeElement.blur();
    window.dispatchEvent(new CustomEvent("talentsync:feedback", { detail: { error: true, message: "Aviso de revisión del rol" } }));
  });
  await expect(page.locator(".feedback-toast")).toHaveClass(new RegExp(`role-${role}`));
  await page.getByRole("button", { name: "Cerrar aviso", exact: true }).click();
  if (width < 600) {
    expect(await description.evaluate((element) => parseFloat(getComputedStyle(element).fontSize))).toBeGreaterThanOrEqual(16);
    await page.getByRole("button", { name: "Abrir menú", exact: true }).click();
    const menu = page.getByRole("dialog", { name: "Navegación principal", exact: true });
    await expect(menu).toBeVisible();
    await expect(menu.getByRole("button", { name: "Cerrar menú", exact: true })).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    expect(await menu.evaluate((element) => element.contains(document.activeElement))).toBe(true);
    await page.keyboard.press("Escape");
    await expect(menu).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Abrir menú", exact: true })).toBeFocused();
  }
  await page.screenshot({ path: `../.local/design-closure-review/${role}-${theme}-${width}.png`, fullPage: true });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});

test("Async confirmation preserves data on failure, blocks repeats and permits retry", async ({ page }) => {
  await setup(page, "candidate", "dark", 360);
  const field = page.getByRole("textbox", { name: "Descripción", exact: true });
  await field.fill("Conservar mi edición");
  const trigger = page.getByRole("button", { name: "Guardar preferencias", exact: true });
  await trigger.click();
  const dialog = page.getByRole("alertdialog", { name: "Guardar preferencias", exact: true });
  await expect(dialog.getByRole("button", { name: "Cancelar", exact: true })).toBeFocused();
  await dialog.getByRole("button", { name: "Confirmar guardado", exact: true }).dblclick();
  await expect(dialog.getByRole("button", { name: "Cancelar", exact: true })).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("alert")).toContainText("No se pudo guardar");
  await expect(page.getByLabel("Intentos de guardado", { exact: true })).toHaveText("1");
  await expect(field).toHaveValue("Conservar mi edición");
  await dialog.getByRole("button", { name: "Confirmar guardado", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.getByLabel("Intentos de guardado", { exact: true })).toHaveText("2");
  await expect(trigger).toBeFocused();
  await trigger.click();
  await expect(dialog.getByRole("button", { name: "Confirmar guardado", exact: true })).toBeEnabled();
  await dialog.getByRole("button", { name: "Cancelar", exact: true }).click();
});

test("Login validation links visible errors to the appropriate fields", async ({ page }) => {
  await page.goto("/quality/?auth=login&theme=dark");
  await page.getByRole("button", { name: "Entrar a mi espacio", exact: true }).click();
  for (const name of ["Correo electrónico", "Contraseña"]) {
    const input = page.getByLabel(name, { exact: true });
    await expect(input).toHaveAttribute("aria-invalid", "true");
    const id = await input.getAttribute("aria-describedby");
    await expect(page.locator(`[id="${id}"]`)).toHaveAttribute("role", "alert");
  }
});

async function contrast(locator, part = "text") {
  return locator.evaluate((element, part) => {
    const style = getComputedStyle(element), canvas = document.createElement("canvas");
    canvas.width = canvas.height = 1;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    function luminance(color) {
      context.clearRect(0, 0, 1, 1); context.fillStyle = color; context.fillRect(0, 0, 1, 1);
      const channels = [...context.getImageData(0, 0, 1, 1).data].slice(0, 3).map((value) => { const v = value / 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; });
      return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
    }
    const foreground = part === "placeholder" ? getComputedStyle(element, "::placeholder").color : part === "border" ? style.borderTopColor : style.color;
    const a = luminance(foreground), b = luminance(style.backgroundColor);
    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
  }, part);
}
