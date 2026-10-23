import { test, expect } from "@playwright/test";

const upcoming = Array.from({ length: 120 }, (_, index) => ({ id: index + 1, job_id: index + 1, job_title: `Especialista de operaciones ${String(index + 1).padStart(3, "0")} · coordinación y seguimiento`, company_name: index === 79 ? "Compañía Única" : "Empresa de ejemplo", status: "technical_interview", created_at: "2026-10-20T14:00:00", interview_at: new Date(Date.UTC(2030, 9, 26 + index, 14)).toISOString(), version: 1, interview_details: { mode: index % 2 ? "in_person" : "virtual", minutes: 45, location: index % 2 ? "Calle 50 # 20-30, oficina 402" : "https://meet.google.com/example", instructions: "Pregunta por el equipo de selección al llegar." } }));
const rows = [...upcoming,
  { ...upcoming[0], id: 121, interview_at: "2000-01-01T14:00:00", job_title: "Entrevista por confirmar" },
  { ...upcoming[0], id: 122, interview_at: "2000-01-02T14:00:00", interview_completed_at: "2000-01-02T15:00:00", job_title: "Entrevista realizada" },
  { ...upcoming[0], id: 123, interview_at: "2000-01-03T14:00:00", status: "hired", job_title: "Proceso finalizado" },
  { ...upcoming[0], id: 124, interview_at: null, status: "submitted", job_title: "Postulación sin cita" }];

async function mockApplications(page, options = {}) {
  const requests = [];
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname.replace("/api/v1", "");
    requests.push(path);
    if (path === "/applications/me") return route.fulfill({ json: rows });
    if (path === "/jobs") return route.fulfill({ json: [] });
    if (/\/workflow\/applications\/\d+\/calendar/.test(path)) return route.fulfill({ json: { state: options.synced ? "synced" : "none", enabled: !!options.synced } });
    if (path === "/account/calendar") return route.fulfill({ json: { configured: true, connected: true } });
    return route.fulfill({ status: 404, json: { detail: "Ruta inesperada" } });
  });
  return requests;
}

for (const width of [360, 1280]) for (const theme of ["light", "dark"]) test(`Candidate processes and bounded agenda · ${width} · ${theme}`, async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width, height: 950 });
  const requests = await mockApplications(page, { synced: true });
  await page.goto(`/quality/?candidateprocesses=1&theme=${theme}`);
  const applications = page.getByRole("tabpanel", { name: "Postulaciones (124)", exact: true });
  const agendaTab = page.getByRole("tab", { name: "Entrevistas (120)", exact: true });
  await expect(applications).toBeVisible();
  await expect(page.getByRole("heading", { name: "Tu agenda de entrevistas" })).toBeHidden();
  await expect(applications.locator('article[id^="application-"]')).toHaveCount(8);
  expect(requests.filter((path) => path.endsWith("/calendar"))).toHaveLength(0);
  await applications.getByRole("navigation", { name: "Páginas de postulaciones" }).getByRole("button", { name: "Siguiente" }).click();
  await expect(applications.locator("#application-9")).toBeVisible();
  await agendaTab.click();
  const agenda = page.getByRole("region", { name: "Agenda de entrevistas", exact: true });
  const pagination = agenda.getByRole("navigation", { name: "Páginas de entrevistas" });
  await expect(applications).toBeHidden();
  await expect(agenda.locator(".candidate-interview-summary")).toHaveCount(6);
  await expect(pagination).toContainText("Página 1 de 20");
  await pagination.getByRole("button", { name: "Siguiente" }).click();
  await expect(pagination).toContainText("Página 2 de 20");
  expect(requests.filter((path) => path.endsWith("/calendar"))).toHaveLength(0);
  await agenda.locator(".candidate-interview-summary").first().click();
  await expect(agenda.getByRole("link", { name: "Abrir videollamada" })).toBeVisible();
  await expect(agenda.getByRole("button", { name: "En Google Calendar", exact: true })).toBeVisible();
  await expect(agenda.getByRole("link", { name: "Ver proceso", exact: true })).toHaveAttribute("href", "/procesos/7");
  await agenda.getByRole("button", { name: "En Google Calendar", exact: true }).click();
  await expect(agenda.getByRole("status")).toContainText("Entrevista sincronizada");
  await expect(agenda.getByRole("link", { name: "Abrir Google Calendar", exact: true })).toBeVisible();
  const calendarBox = await agenda.locator(".calendar-sync-options").boundingBox(), agendaBox = await agenda.boundingBox();
  expect(calendarBox.x).toBeGreaterThanOrEqual(agendaBox.x);
  expect(calendarBox.x + calendarBox.width).toBeLessThanOrEqual(agendaBox.x + agendaBox.width);
  if (width < 600) {
    const processBox = await agenda.getByRole("link", { name: "Ver proceso", exact: true }).boundingBox();
    const triggerBox = await agenda.getByRole("button", { name: "En Google Calendar", exact: true }).boundingBox();
    expect(triggerBox.y).toBeGreaterThanOrEqual(processBox.y + processBox.height);
  }
  await page.screenshot({ path: `../.local/candidate-agenda-review/calendar-${theme}-${width}.png`, fullPage: true });
  await agenda.locator(".candidate-interview-summary").nth(1).click();
  await expect(agenda.locator(".candidate-interview-expanded")).toHaveCount(1);
  await expect(agenda.getByText("Calle 50 # 20-30, oficina 402", { exact: true })).toBeVisible();
  await page.screenshot({ path: `../.local/candidate-agenda-review/expanded-${theme}-${width}.png`, fullPage: true });
  await agenda.getByLabel("Buscar entrevista por empresa o vacante").fill("compania unica");
  await expect(agenda.locator(".candidate-interview-summary")).toHaveCount(1);
  await expect(pagination).toContainText("Página 1 de 1");
  await agenda.getByLabel("Modalidad de la entrevista", { exact: true }).selectOption("virtual");
  await expect(agenda.getByRole("heading", { name: "No hay citas con estos filtros" })).toBeVisible();
  await agenda.getByRole("button", { name: "Limpiar filtros", exact: true }).click();
  await expect(agenda.locator(".candidate-interview-summary")).toHaveCount(6);
  await agenda.getByRole("button", { name: "Pendientes 2", exact: true }).click();
  await expect(agenda.locator(".candidate-interview-summary")).toHaveCount(2);
  await expect(agenda.getByText("Por confirmar realización", { exact: true })).toBeVisible();
  await expect(agenda.getByText("Esperando respuesta", { exact: true })).toBeVisible();
  await agenda.locator(".candidate-interview-summary").first().click();
  await expect(agenda.getByRole("button", { name: /Google Calendar/ })).toHaveCount(0);
  await agenda.getByRole("button", { name: "Historial 1", exact: true }).click();
  await agenda.locator(".candidate-interview-summary").first().click();
  await expect(agenda.getByRole("button", { name: /Google Calendar/ })).toHaveCount(0);
  await agenda.getByRole("button", { name: "Próximas 120", exact: true }).click();
  await pagination.getByRole("button", { name: "Siguiente" }).click();
  await page.getByRole("tab", { name: "Postulaciones (124)", exact: true }).click();
  await expect(applications.locator("#application-9")).toBeVisible();
  await agendaTab.click();
  await expect(pagination).toContainText("Página 2 de 20");
  await page.screenshot({ path: `../.local/candidate-agenda-review/list-${theme}-${width}.png`, fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});

test("Candidate agenda supports direct navigation and an application focus takes precedence", async ({ page }) => {
  await mockApplications(page);
  await page.goto("/quality/?candidateprocesses=1&section=interviews");
  await expect(page.getByRole("tab", { name: "Entrevistas (120)", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.goto("/quality/?candidateprocesses=1&section=interviews&focus=100");
  await expect(page.getByRole("tab", { name: "Postulaciones (124)", exact: true })).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("#application-100")).toBeVisible();
  await page.getByRole("tab", { name: "Entrevistas (120)", exact: true }).click();
  await expect(page.getByRole("region", { name: "Agenda de entrevistas", exact: true })).toBeVisible();
});

test("Candidate agenda recovers a load failure without showing an empty agenda", async ({ page }) => {
  let ready = false;
  await page.route("**/api/v1/**", (route) => {
    if (new URL(route.request().url()).pathname.endsWith("/applications/me")) return route.fulfill(ready ? { json: [] } : { status: 503, json: { detail: "No pudimos consultar tus entrevistas" } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/quality/?candidateprocesses=1&section=interviews");
  await expect(page.getByRole("alert")).toContainText("No pudimos consultar tus entrevistas");
  await expect(page.getByRole("heading", { name: "Sin entrevistas próximas", exact: true })).toHaveCount(0);
  ready = true;
  await page.getByRole("button", { name: "Reintentar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sin entrevistas próximas", exact: true })).toBeVisible();
});
