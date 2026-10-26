import { test, expect } from "@playwright/test";

async function setup(page, { role = "candidate", width = 1280, theme = "light", path = "/guia", member = "owner" } = {}) {
  const calls = [], errors = [];
  await page.setViewportSize({ width, height: 950 });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const request = route.request(), url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    const endpoint = url.pathname.replace("/api/v1", ""); calls.push({ endpoint, method: request.method() });
    if (endpoint === "/notifications/unread-count") return route.fulfill({ json: { count: 3 } });
    if (["/organization/me", "/organization/access"].includes(endpoint)) return route.fulfill({ json: { active: true, role: member, name: "Organización de revisión", verification_status: "verified" } });
    if (endpoint === "/account/privacy") return route.fulfill({ json: { share_evidence: false, notify_new_skills: false, personalize_recommendations: false } });
    if (endpoint === "/account/sessions") return route.fulfill({ json: [] });
    if (endpoint === "/account/social-identities") return route.fulfill({ json: [{ provider: "google" }, { provider: "github" }] });
    if (endpoint === "/account/calendar") return route.fulfill({ json: { configured: true, connected: true, needs_reconnect: false } });
    if (endpoint === "/account/data") return route.fulfill({ json: { deletion_block: "", note: "Retira la cuenta y cierra sus sesiones." } });
    return route.fulfill({ status: 404, json: { detail: "Ruta no prevista en esta revisión" } });
  });
  await page.goto(`/quality/?entry=1&signed=${role}&theme=${theme}&path=${encodeURIComponent(path)}`);
  return { calls, errors };
}

async function noOverflow(page) {
  const geometry = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth, elements: [...document.querySelectorAll("main *")].filter((node) => node.getBoundingClientRect().right > innerWidth + 1).slice(0, 10).map((node) => ({ tag: node.tagName, class: String(node.className), width: Math.round(node.getBoundingClientRect().width) })) }));
  expect(geometry.overflow, JSON.stringify(geometry)).toBeLessThanOrEqual(1);
}

for (const role of ["candidate", "company", "admin"]) for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Guide and navigation · ${role} · ${theme} · ${width}`, async ({ page }) => {
  const context = await setup(page, { role, width, theme });
  await expect(page.getByRole("heading", { name: "Cómo usar TalentSync", exact: true })).toBeVisible();
  const topicIcons = await page.locator(".guide-topic-group button>svg:first-child").evaluateAll((nodes) => nodes.map((node) => [...node.classList].find((name) => name.startsWith("lucide-"))));
  expect(new Set(topicIcons).size).toBe(topicIcons.length);
  const choose = async (id, title) => {
    if (width < 850) await page.getByRole("combobox", { name: "Tema de la guía", exact: true }).selectOption(id);
    else await page.getByRole("navigation", { name: "Temas de la guía", exact: true }).getByRole("button", { name: title, exact: true }).click();
  };
  const qualityTitle = role === "candidate" ? "Calidad y claridad de las ofertas" : role === "company" ? "Interpretar la calidad de una oferta" : "Claridad, compatibilidad y confianza";
  await choose("quality", qualityTitle);
  await expect(page.getByRole("heading", { name: qualityTitle, exact: true })).toBeVisible();
  await expect(page.locator(".guide-explanations>section")).not.toHaveCount(0);
  await page.screenshot({ path: `../.local/guide-navigation-review/guide-${role}-${theme}-${width}.png`, fullPage: true });
  if (role === "candidate") {
    await page.getByRole("textbox", { name: "Buscar en la guía", exact: true }).fill("comparar");
    await choose("compare", "Comparar vacantes");
    await expect(page.getByRole("heading", { name: "Comparar vacantes", exact: true })).toBeVisible();
    await expect(page.locator(".platform-guide-content")).toContainText("hasta tres");
    await page.getByRole("button", { name: "Limpiar búsqueda de la guía", exact: true }).click();
    await choose("saved", "Guardar y ocultar oportunidades");
    await expect(page.getByRole("link", { name: "Ver mis guardadas", exact: true })).toHaveAttribute("href", "/vacantes?interes=saved");
  }
  await page.getByRole("textbox", { name: "Buscar en la guía", exact: true }).fill("zzzzsincoincidencia");
  await expect(page.getByRole("heading", { name: "No hay temas con esta búsqueda", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Ver todos los temas", exact: true }).click();
  if (width < 1024) await page.getByRole("button", { name: "Abrir menú", exact: true }).click();
  const navigation = width < 1024 ? page.getByRole("dialog", { name: "Navegación principal", exact: true }) : page.locator("aside.app-sidebar").first();
  const icons = await navigation.locator(".app-nav-link .app-nav-icon svg").evaluateAll((nodes) => nodes.map((node) => [...node.classList].find((name) => name.startsWith("lucide-"))));
  expect(icons.length).toBeGreaterThan(4);
  expect(new Set(icons).size).toBe(icons.length);
  await expect(navigation.getByRole("link", { name: "Guía de uso", exact: true })).toHaveAttribute("aria-current", "page");
  await navigation.screenshot({ path: `../.local/guide-navigation-review/navigation-${role}-${theme}-${width}.png` });
  if (width < 1024) await navigation.getByRole("button", { name: "Cerrar menú", exact: true }).click();
  await noOverflow(page);
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await noOverflow(page);
  expect(context.calls.every((row) => row.method === "GET")).toBe(true);
  expect(context.errors).toEqual([]);
});

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Security actions preserve confirmations and data · ${theme} · ${width}`, async ({ page }) => {
  const context = await setup(page, { theme, width, path: "/seguridad" });
  const change = page.getByRole("button", { name: "Cambiar correo", exact: true });
  await change.click();
  await expect(page.getByRole("textbox", { name: "Nuevo correo", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "Nuevo correo", exact: true })).toHaveCount(0);
  const unlink = page.getByRole("button", { name: "Desvincular Google", exact: true });
  await unlink.click();
  await expect(page.getByRole("heading", { name: "Desvincular Google", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.screenshot({ path: `../.local/guide-navigation-review/security-email-${theme}-${width}.png`, fullPage: true });
  await page.locator('.security-section-nav a[href$="#security-calendar"]').click();
  await page.getByRole("button", { name: "Desconectar", exact: true }).click();
  const dialog = page.getByRole("alertdialog", { name: "Desconectar Google Calendar", exact: true });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(page.getByText("Calendario conectado", { exact: true })).toBeVisible();
  await page.locator('.security-section-nav a[href$="#security-data"]').click();
  await page.getByRole("button", { name: "Preparar descarga", exact: true }).click();
  await expect(page.getByRole("button", { name: "Descargar copia ZIP", exact: true })).toBeVisible();
  await page.screenshot({ path: `../.local/guide-navigation-review/security-data-${theme}-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  await page.getByRole("button", { name: "Solicitar eliminación", exact: true }).click();
  await expect(page.getByRole("button", { name: "Eliminar mi cuenta", exact: true })).toHaveClass(/button-danger/);
  await page.getByRole("button", { name: "Cancelar", exact: true }).click();
  for (const control of await page.locator(".security-content button").all()) {
    if (await control.isVisible()) expect((await control.boundingBox()).height).toBeGreaterThanOrEqual(44);
  }
  await noOverflow(page);
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; }); await noOverflow(page);
  expect(context.calls.every((row) => row.method === "GET")).toBe(true);
  expect(context.errors).toEqual([]);
});
