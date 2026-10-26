import { test, expect } from "@playwright/test";

const baseProfile = { profession: "Ingeniero de Sistemas", location: "Medellín", department: "Antioquia", preferred_modality: "remote", desired_salary: 3500000, preferred_sector: "Tecnología", availability: "immediate", skills: ["react"], experiences: [], educations: [], certifications: [], languages: [], links: [], mobility: {} };
async function setup(page, { role = "candidate", path = "/preferencias", pending = false, width = 1280, theme = "light", history = false, realSession = false } = {}) {
  await page.setViewportSize({ width, height: 1000 });
  await page.addInitScript((theme) => localStorage.setItem("talentsync_theme", theme), theme);
  const state = { user: { id: 101, role, name: "Persona de revisión", email: "person@example.com", email_verified: true, mfa_enabled: true, registration_pending: pending }, profile: structuredClone(baseProfile), failWrite: false };
  const savedUser = structuredClone(state.user);
  if (realSession) state.user = null;
  const writes = [], errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const request = route.request(), url = new URL(request.url()), endpoint = url.pathname.replace("/api/v1", "");
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    if (request.method() !== "GET") writes.push({ endpoint, body: request.postDataJSON() });
    if (endpoint === "/profiles/me") {
      if (request.method() === "PUT") {
        if (state.failWrite) return route.fulfill({ status: 503, json: { detail: "No se pudo guardar. Intenta de nuevo." } });
        state.profile = { ...state.profile, ...request.postDataJSON() };
      }
      return route.fulfill({ json: state.profile });
    }
    if (endpoint === "/auth/options") return route.fulfill({ json: { mode: "session", providers: [], company_mfa_required: false, admin_mfa_required: false } });
    if (endpoint === "/auth/me") return state.user ? route.fulfill({ json: state.user }) : route.fulfill({ status: 401, json: { detail: "Sin sesión" } });
    if (/^\/auth\/session\/(candidate|company)\/login$/.test(endpoint)) { state.user = savedUser; return route.fulfill({ json: { user: state.user, mfa_required: false } }); }
    if (/^\/auth\/(candidate|company)\/register$/.test(endpoint)) return route.fulfill({ json: { ...savedUser, ...request.postDataJSON() } });
    if (endpoint === "/auth/social/registration") { state.user = { ...state.user, registration_pending: false, name: request.postDataJSON().name }; return route.fulfill({ json: state.user }); }
    if (endpoint.endsWith("unread-count")) return route.fulfill({ json: { count: 0 } });
    if (endpoint === "/companies/me") return route.fulfill({ json: { id: 1, name: "Empresa de revisión", nit: "TEST-ONLY", sector: "Tecnología", location: "Bogotá", values: [], benefits: [] } });
    if (["/organization/me", "/organization/access"].includes(endpoint)) return route.fulfill({ json: { id: 1, name: "Empresa de revisión", role: "owner", verification_required: false, verification_status: "pending" } });
    if (endpoint === "/account/privacy") return route.fulfill({ json: { personalize_recommendations: false } });
    if (endpoint === "/matching/preferences") return route.fulfill({ json: {} });
    if (endpoint === "/recommendations/me/jobs/batch") return route.fulfill({ json: { items: [], pending: 0 } });
    return route.fulfill({ json: [] });
  });
  const params = new URLSearchParams({ entry: "1", signed: role, path, ...(pending ? { registration: "pending" } : {}), ...(history ? { history: "1" } : {}), ...(realSession ? { session: "real" } : {}) });
  await page.goto(`/quality/?${params}`);
  return { state, writes, errors };
}
const output = (page) => page.getByLabel("Ruta de revisión", { exact: true });
async function noOverflow(page) { expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1); }

for (const role of ["candidate", "company", "admin"]) test(`Signed ${role} cannot return to any login or registration`, async ({ page }) => {
  const destination = role === "candidate" ? "/candidato" : role === "company" ? "/empresa" : "/admin";
  for (const path of ["/login", "/registro", "/empresa/login", "/empresa/registro", "/acceso-administracion"]) {
    await setup(page, { role, path });
    await expect(output(page)).toHaveText(destination);
    await expect(page.locator('input[type="password"]')).toHaveCount(0);
  }
});

test("A fresh password login reaches its workspace with the real auth context", async ({ page }) => {
  const context = await setup(page, { path: "/login", realSession: true });
  await page.getByLabel("Correo electrónico", { exact: true }).fill("person@example.com");
  await page.getByLabel("Contraseña", { exact: true }).fill("Synthetic-pass-2026!");
  await page.getByRole("button", { name: "Entrar a mi espacio", exact: true }).click();
  await expect(output(page)).toHaveText("/candidato");
  expect(context.errors).toEqual([]);
});

test("A new email registration reaches welcome rather than being intercepted by guest guards", async ({ page }) => {
  const context = await setup(page, { path: "/registro", realSession: true });
  await page.getByLabel("Nombre completo", { exact: true }).fill("Persona de revisión");
  await page.getByLabel("Correo electrónico", { exact: true }).fill("person@example.com");
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await page.getByLabel("Profesión o cargo de interés", { exact: true }).fill("Analista");
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await page.getByLabel("Crea tu contraseña", { exact: true }).fill("Synthetic-pass-2026!");
  await page.getByLabel("Repite tu contraseña", { exact: true }).fill("Synthetic-pass-2026!");
  await page.getByRole("button", { name: "Continuar", exact: true }).click();
  await page.getByRole("button", { name: "Confirmar y crear cuenta", exact: true }).click();
  await expect(output(page)).toHaveText("/bienvenida");
  expect(context.errors).toEqual([]);
});

test("Back navigation to a login with an active session returns to the workspace", async ({ page }) => {
  const context = await setup(page, { path: "/preferencias", history: true });
  await expect(page.getByRole("heading", { name: "Ajusta tu búsqueda" })).toBeVisible();
  await page.getByRole("button", { name: "Atrás en revisión" }).click();
  await expect(output(page)).toHaveText("/candidato");
  await expect(page.getByRole("link", { name: "Ajustar mi búsqueda", exact: true })).toHaveAttribute("href", "/preferencias");
  expect(context.errors).toEqual([]);
});

for (const width of [360, 1440]) for (const theme of ["light", "dark"]) test(`Search settings share profile fields · ${width} · ${theme}`, async ({ page }) => {
  const context = await setup(page, { width, theme });
  await expect(page.getByRole("heading", { name: "Ajusta tu búsqueda" })).toBeVisible();
  await expect(page.locator(".platform-guide")).toHaveCount(0);
  await expect(page.getByLabel("Cargo o área de interés", { exact: true })).toHaveValue(baseProfile.profession);
  await expect(page.getByLabel("Modalidad", { exact: true })).toHaveValue("remote");
  await page.getByLabel("Modalidad", { exact: true }).selectOption("hybrid");
  context.state.profile = { ...context.state.profile, phone: "3000000000", skills: ["react", "sql"] };
  context.state.failWrite = true;
  await page.getByRole("button", { name: "Guardar preferencias", exact: true }).click();
  await expect(page.locator(".welcome-error")).toContainText("No se pudo guardar");
  await expect(page.getByLabel("Modalidad", { exact: true })).toHaveValue("hybrid");
  await noOverflow(page);
  await page.screenshot({ path: `../.local/access-preferences/search-${theme}-${width}.png`, fullPage: true });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await noOverflow(page);
  context.state.failWrite = false;
  await page.getByRole("button", { name: "Guardar preferencias", exact: true }).click();
  await expect(output(page)).toHaveText("/recomendaciones");
  expect(context.writes.at(-1).body).toMatchObject({ preferred_modality: "hybrid", phone: "3000000000", skills: ["react", "sql"] });
  expect(context.errors).toEqual([]);
});

for (const width of [360, 1440]) test(`Company profile uses available width · ${width}`, async ({ page }) => {
  const context = await setup(page, { role: "company", path: "/empresa/perfil", width, theme: "dark" });
  await expect(page.getByRole("textbox", { name: "Nombre de la empresa", exact: true })).toHaveValue("Empresa de revisión");
  const widths = await page.evaluate(() => [document.querySelector(".company-settings-page").clientWidth, document.querySelector(".company-settings-form").getBoundingClientRect().width]);
  expect(Math.abs(widths[0] - widths[1])).toBeLessThanOrEqual(2);
  await noOverflow(page);
  await page.screenshot({ path: `../.local/access-preferences/company-${width}.png`, fullPage: true });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await noOverflow(page);
  expect(context.errors).toEqual([]);
});

for (const width of [360, 1280]) test(`Social registration confirms identity before access · ${width}`, async ({ page }) => {
  const context = await setup(page, { pending: true, path: "/login", width, theme: "dark" });
  await expect(output(page)).toHaveText("/completar-cuenta");
  await expect(page.getByRole("heading", { name: "Presentémonos bien" })).toBeVisible();
  expect(context.writes).toEqual([]);
  await page.getByLabel("Tu nombre", { exact: true }).fill("Ana María García");
  await page.getByLabel("Profesión o cargo de interés", { exact: true }).fill("Ingeniera de Sistemas");
  await page.getByRole("checkbox").check();
  await noOverflow(page);
  await page.screenshot({ path: `../.local/access-preferences/registration-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: "Confirmar y continuar", exact: true }).click();
  await expect(output(page)).toHaveText("/bienvenida");
  expect(context.writes).toEqual([{ endpoint: "/auth/social/registration", body: { name: "Ana María García", profession: "Ingeniera de Sistemas", confirmed: true } }]);
  expect(context.errors).toEqual([]);
});
