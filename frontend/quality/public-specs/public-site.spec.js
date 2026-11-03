import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

const documents = JSON.parse(readFileSync(new URL("../../../backend/legal_documents/current.json", import.meta.url), "utf8"));

async function scrollbarMatchesRole(page) {
  const palette = await page.evaluate(() => {
    const root = getComputedStyle(document.documentElement), role = getComputedStyle(document.querySelector(".public-site"));
    return { thumb: root.getPropertyValue("--scrollbar-accent").trim(), track: root.getPropertyValue("--scrollbar-track").trim(), accent: role.getPropertyValue("--accent").trim(), canvas: role.getPropertyValue("--canvas").trim() };
  });
  expect(palette.thumb).toBe(palette.accent);
  expect(palette.track).toBe(palette.canvas);
}

for (const theme of ["light", "dark"]) for (const width of [360, 1366]) test(`Role landings and legal navigation · ${theme} · ${width}`, async ({ page }) => {
  const errors = [], apiRequests = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => { if (/\/api\/|azurecontainerapps/.test(request.url())) apiRequests.push(request.url()); });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  await page.setViewportSize({ width, height: 950 });
  const fits = async () => expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Encuentra tu lugar");
  await scrollbarMatchesRole(page);
  await expect(page.locator('a[href="/login"], a[href="/registro"], a[href="/empresa/registro"]')).toHaveCount(0);
  await expect(page.getByText(/administrador|administración/i)).toHaveCount(0);
  const candidateAccent = await page.locator(".role-landing").evaluate((element) => getComputedStyle(element).getPropertyValue("--accent"));
  await page.getByRole("checkbox", { name: "Comunicación", exact: true }).check();
  await expect(page.locator(".role-demo-match strong")).toContainText("2");
  await fits();
  await page.screenshot({ path: `../.local/public-site/candidate-${theme}-${width}.png`, fullPage: true });
  await page.getByRole("navigation", { name: "Elige tu espacio" }).getByRole("link", { name: "Para empresas" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Encuentra talento");
  await scrollbarMatchesRole(page);
  const companyAccent = await page.locator(".role-landing").evaluate((element) => getComputedStyle(element).getPropertyValue("--accent"));
  expect(companyAccent).not.toBe(candidateAccent);
  await page.getByRole("button", { name: /Entrevista/ }).click();
  await expect(page.locator(".company-demo-stage")).toHaveText("Entrevista");
  await expect(page.locator(".role-capabilities article")).toHaveCount(6);
  await fits();
  await page.screenshot({ path: `../.local/public-site/company-${theme}-${width}.png`, fullPage: true });
  await page.locator("footer.public-footer").getByRole("link", { name: "Privacidad", exact: true }).click();
  await expect(page).toHaveURL(/privacidad\?rol=empresa/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Privacidad y tratamiento de datos");
  await expect(page.locator(".legal-site")).toHaveClass(/role-company/);
  await scrollbarMatchesRole(page);
  await expect(page.locator(".legal-version")).toContainText(documents.privacy_version);
  await expect(page.locator(".legal-contact")).toContainText("José Alejandro Blanquicett Herrera");
  await expect(page.locator(".legal-contact")).toContainText("Medellín, Colombia");
  await expect(page.locator(".legal-draft")).toHaveCount(0);
  await page.getByRole("navigation", { name: "En este documento" }).getByRole("link", { name: /Google, GitHub y calendario/ }).click();
  await expect(page.locator("#google")).toContainText("ni leemos sus mensajes");
  await fits();
  await page.goto("/privacidad");
  await scrollbarMatchesRole(page);
  await page.screenshot({ path: `../.local/public-site/privacy-${theme}-${width}.png`, fullPage: false });
  await page.getByRole("navigation", { name: "Documentos legales" }).getByRole("link", { name: "Términos de uso", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Términos de uso");
  await fits();
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "El acceso a cuentas está en preparación" })).toBeVisible();
  await expect(page.locator("input, form")).toHaveCount(0);
  expect(apiRequests).toEqual([]);
  expect(errors).toEqual([]);
});

test("All public routes include readable HTML without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  for (const [path, title] of [["/", "Encuentra tu lugar"], ["/candidatos/", "Encuentra tu lugar"], ["/empresas/", "Encuentra talento"], ["/privacidad/", "Privacidad y tratamiento"], ["/terminos/", "Términos de uso"]]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(title);
    await scrollbarMatchesRole(page);
    await expect(page.locator('meta[name="google-site-verification"]')).toHaveCount(1);
  }
  await context.close();
});
