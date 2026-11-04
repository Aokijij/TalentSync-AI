import { test, expect } from "@playwright/test";

const baseProfile = { profession: "Analista de datos", location: "Bogotá", department: "Bogotá D.C.", preferred_modality: "onsite", desired_salary: 2500000, skills: ["excel"], experiences: [{ role: "Analista", company: "Equipo de revisión" }], educations: [], certifications: [], languages: [], links: [], preferences: {}, mobility: {}, phone: "3000000000" };
const baseOrganization = { id: 41, name: "Organización para revisión de interfaz", nit: "IDENTIFICACIÓN DE PRUEBA", active: true, role: "owner", verification_required: true, verification_status: "reviewing", submission: { submitted_at: "2026-10-23T09:00:00Z" }, feedback: null };
async function setup(page, { screen = "landing", theme = "light", width = 1280, status = "reviewing", role, path, email = "confirmed" } = {}) {
  await page.setViewportSize({ width, height: 950 });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  const calls = [], errors = [];
  const state = { profile: structuredClone(baseProfile), organization: { ...baseOrganization, verification_status: status }, jobs: [], failRead: false, failWrite: false };
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const request = route.request(), url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    const endpoint = url.pathname.replace("/api/v1", ""), method = request.method();
    calls.push({ endpoint, method, body: request.postDataJSON() });
    if (endpoint === "/profiles/me") {
      if (state.failRead && method === "GET") return route.fulfill({ status: 503, json: { detail: "No se pudo cargar el perfil de revisión." } });
      if (method === "PUT") {
        if (state.failWrite) return route.fulfill({ status: 503, json: { detail: "No se pudo guardar. Tus preferencias siguen aquí." } });
        state.profile = { ...state.profile, ...request.postDataJSON() };
      }
      return route.fulfill({ json: state.profile });
    }
    if (endpoint === "/auth/me") return route.fulfill({ json: { id: 101, name: "Persona de revisión", role: "candidate", email: "person@example.com" } });
    if (["/organization/me", "/organization/access"].includes(endpoint)) return route.fulfill({ json: state.organization });
    if (endpoint === "/companies/me") return route.fulfill({ json: state.organization });
    if (endpoint === "/jobs") return route.fulfill({ json: state.jobs });
    if (endpoint.startsWith("/applications/jobs/")) return route.fulfill({ json: [] });
    if (endpoint.endsWith("/notifications/unread-count")) return route.fulfill({ json: { count: 0 } });
    if (endpoint === "/recommendations/me/jobs/batch") return route.fulfill({ json: { items: [], pending: 0 } });
    if (endpoint === "/account/privacy") return route.fulfill({ json: { personalize_recommendations: false } });
    if (endpoint === "/matching/preferences") return route.fulfill({ json: {} });
    if (["/applications/me", "/jobs", "/learning/plans", "/personalization/feedback", "/matching/evidence", "/organization/assignments"].includes(endpoint)) return route.fulfill({ json: [] });
    return route.fulfill({ status: 404, json: { detail: "Ruta no prevista en esta prueba" } });
  });
  const signed = role || (screen === "landing" ? "" : screen);
  const params = new URLSearchParams({ entry: "1", theme, email, path: path || (screen === "candidate" ? "/bienvenida" : screen === "company" ? "/empresa/bienvenida" : "/"), ...(signed ? { signed } : {}) });
  return { calls, errors, state, open: () => page.goto(`/quality/?${params}`) };
}
const routeOutput = (page) => page.getByLabel("Ruta de revisión", { exact: true });
async function expectLayout(page) {
  const result = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth, elements: [...document.querySelectorAll("body *")].filter((node) => node.getBoundingClientRect().right > innerWidth + 1).slice(0, 10).map((node) => ({ tag: node.tagName, class: String(node.className), width: Math.round(node.getBoundingClientRect().width) })) }));
  expect(result.overflow, JSON.stringify(result.elements)).toBeLessThanOrEqual(1);
}

for (const screen of ["landing", "candidate", "company"]) for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Entry experience · ${screen} · ${theme} · ${width}`, async ({ page }) => {
  const context = await setup(page, { screen, theme, width }); await context.open();
  const title = screen === "landing" ? /Encuentra tu lugar/ : screen === "candidate" ? "Empieza por lo que buscas" : "Prepara tu espacio de empresa";
  await expect(page.getByRole("heading", { level: 1, name: title })).toBeVisible();
  if (screen === "landing") {
    await expect(page.locator(".public-hero-actions a").first()).toHaveAttribute("href", "/registro");
    await expect(page.getByRole("navigation", { name: "Elige tu espacio" }).getByRole("link", { name: "Para empresas" })).toHaveAttribute("href", "/empresas");
    await expect(page.locator(".role-preview footer")).toContainText("Datos ficticios");
    await page.getByRole("checkbox", { name: "Análisis de datos", exact: true }).check();
    await expect(page.locator(".role-demo-match strong")).toContainText("67");
    await page.getByRole("checkbox", { name: "Comunicación", exact: true }).check();
    await expect(page.locator(".role-demo-match strong")).toContainText("100");
    expect(context.calls).toEqual([]);
  } else if (screen === "candidate") {
    await expect(page.getByLabel("Cargo o área de interés", { exact: true })).toHaveValue(baseProfile.profession);
    await expect(page.getByLabel("Modalidad", { exact: true })).toHaveValue("onsite");
    await expect(page.getByRole("button", { name: "Ver oportunidades", exact: true })).toBeEnabled();
  } else {
    await expect(page.getByText("En revisión", { exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Preparar un borrador", exact: true })).toHaveAttribute("href", "/empresa/calidad?nueva=1");
    await expect(page.getByText("Acceso habilitado", { exact: true })).toHaveCount(0);
  }
  await expectLayout(page);
  await page.screenshot({ path: `../.local/entry-review/${screen}-${theme}-${width}.png`, fullPage: true });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expectLayout(page);
  expect(context.errors).toEqual([]);
});

test("Candidate welcome retains edits after failure and preserves fresh unrelated profile information", async ({ page }) => {
  const context = await setup(page, { screen: "candidate", width: 360, theme: "dark" }); await context.open();
  const profession = page.getByLabel("Cargo o área de interés", { exact: true });
  await expect(profession).toHaveValue(baseProfile.profession);
  await profession.fill("Analista de operaciones");
  await page.getByRole("button", { name: "Completar después", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Seguir editando", exact: true }).click();
  await expect(profession).toHaveValue("Analista de operaciones");
  context.state.profile = { ...context.state.profile, phone: "3001111111", skills: ["excel", "sql"], preferred_modality: "hybrid" };
  context.state.failWrite = true;
  await page.getByRole("button", { name: "Guardar y ver oportunidades", exact: true }).click();
  await expect(page.locator(".welcome-error")).toContainText("No se pudo guardar");
  await expect(profession).toHaveValue("Analista de operaciones");
  await expect(routeOutput(page)).toHaveText("/bienvenida");
  context.state.failWrite = false;
  await page.getByRole("button", { name: "Guardar y ver oportunidades", exact: true }).click();
  await expect(routeOutput(page)).toHaveText("/recomendaciones");
  const writes = context.calls.filter((row) => row.method === "PUT");
  expect(writes).toHaveLength(2);
  expect(writes[1].body).toMatchObject({ profession: "Analista de operaciones", phone: "3001111111", preferred_modality: "hybrid", skills: ["excel", "sql"], experiences: baseProfile.experiences });
  await expect(page.getByText(/No encontramos|No hay|Aún no/).first()).toBeVisible();
  expect(context.errors).toEqual([]);
});

test("Candidate can postpone without writing or go directly to the existing CV control", async ({ page }) => {
  const context = await setup(page, { screen: "candidate" }); await context.open();
  await expect(page.getByRole("button", { name: "Ver oportunidades", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Completar después", exact: true }).click();
  await expect(routeOutput(page)).toHaveText("/vacantes");
  expect(context.calls.filter((row) => row.method !== "GET")).toEqual([]);
  await context.open();
  await expect(page.getByRole("button", { name: "Ver oportunidades", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Ir a subir mi CV", exact: true }).click();
  await expect(routeOutput(page)).toHaveText("/perfil#profile-cv");
  await expect(page.locator("#profile-cv")).toBeFocused();
  expect(context.errors).toEqual([]);
});

test("Candidate load failure blocks profile replacement and can recover", async ({ page }) => {
  const context = await setup(page, { screen: "candidate" }); context.state.failRead = true; await context.open();
  await expect(page.getByRole("alert").filter({ hasText: "No se pudo cargar" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Ver oportunidades", exact: true })).toBeDisabled();
  expect(context.calls.filter((row) => row.method === "PUT")).toEqual([]);
  context.state.failRead = false;
  await page.getByRole("button", { name: "Reintentar", exact: true }).click();
  await expect(page.getByLabel("Cargo o área de interés", { exact: true })).toHaveValue(baseProfile.profession);
});

test("Company checklist distinguishes corrections, exemption and suspension from approval", async ({ page }) => {
  const context = await setup(page, { screen: "company" });
  for (const [status, label] of [["pending", "Por presentar"], ["information_required", "Requiere correcciones"], ["rejected", "Solicitud rechazada"], ["verified", "Verificada"]]) {
    context.state.organization = { ...baseOrganization, verification_status: status, feedback: status === "information_required" ? "Debes actualizar el soporte de registro de la empresa." : null };
    await context.open();
    await expect(page.locator(".welcome-step-title>span").filter({ hasText: label }).first()).toBeVisible();
    if (status === "verified") await expect(page.getByRole("link", { name: "Preparar una vacante", exact: true })).toBeVisible();
    else await expect(page.getByRole("link", { name: "Preparar un borrador", exact: true })).toBeVisible();
  }
  context.state.organization = { ...baseOrganization, verification_required: false, verification_status: "pending" };
  await context.open();
  await expect(page.getByText(/Esto no equivale a una aprobación administrativa/)).toBeVisible();
  context.state.organization.verification_status = "suspended";
  await context.open();
  await expect(page.getByRole("heading", { name: "La empresa está suspendida", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Preparar una vacante", exact: true })).toHaveCount(0);
  expect(context.calls.filter((row) => row.method !== "GET")).toEqual([]);
  expect(context.errors).toEqual([]);
});

test("Welcome routes retain authentication and company role boundaries", async ({ page }) => {
  const anonymous = await setup(page, { path: "/empresa/bienvenida" }); await anonymous.open();
  await expect(routeOutput(page)).toHaveText("/empresa/login");
  const candidate = await setup(page, { role: "candidate", path: "/empresa/bienvenida" }); await candidate.open();
  await expect(routeOutput(page)).toHaveText("/candidato");
  await expect(page.getByRole("heading", { name: "Prepara tu espacio de empresa", exact: true })).toHaveCount(0);
  expect(candidate.calls.some((row) => row.endpoint === "/organization/me")).toBe(false);
});

test("Company dashboard opens a new offer or the specific draft without selecting another vacancy", async ({ page }) => {
  const context = await setup(page, { screen: "company", path: "/empresa" });
  context.state.jobs = [{ id: 501, company_id: 41, title: "Borrador de revisión de interfaz", status: "draft" }];
  await context.open();
  await expect(page.getByRole("heading", { name: "Así van tus contrataciones", exact: true })).toBeVisible();
  const draft = page.getByRole("link", { name: /Borrador de revisión de interfaz/ });
  await expect(draft).toHaveAttribute("href", "/empresa/calidad?vacante=501");
  await expect(page.getByRole("link", { name: "Crear una vacante", exact: true })).toHaveAttribute("href", "/empresa/calidad?nueva=1");
  await draft.click();
  await expect(routeOutput(page)).toHaveText("/empresa/calidad?vacante=501");
  await expect.poll(() => context.calls.some((row) => row.endpoint === "/hiring/quality/501")).toBe(true);
  expect(context.errors).toEqual([]);
});
