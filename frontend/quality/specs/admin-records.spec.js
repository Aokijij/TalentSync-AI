import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Administrative records support review and editorial decisions · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1050 });
  const calls = [], errors = [];
  let fail = true;
  let job = { id: 41, title: "Analista de datos · Demostración", company_name: "TalentSync · Demostración", company_id: 21, status: "active", source_kind: "external", source_portal: "Portal de ejemplo", skills: ["sql", "excel", "python"], salary: 3000000, location: "Medellín", modality: "hybrid", moderation_status: "automatic", moderation_revision: 0, moderation_note: "", external_available: true, external_check_state: "verified", description: "Prepara reportes y revisa la calidad de los datos.", requirements: "Experiencia con consultas SQL y reportes en Excel.", review: { can_publish: true, score: null, checks: [{ label: "Vigencia comprobada", passed: true }] }, history: [] };
  const account = { id: 11, name: "Candidato 01", email: "candidate01@example.test", role: "candidate", profession: "Analista", skills: ["sql"], profile: { profession: "Analista", skills: ["sql"], experiences_count: 2, educations_count: 1, certifications_count: 0, languages: [], has_cv: true }, applications: [{ id: 4, job_id: 41, job_title: job.title, status: "submitted" }] };
  const company = { id: 21, name: "TalentSync · Demostración", source_kind: "internal", verification_status: "verified", sector: "Tecnología", jobs_count: 1, jobs: [{ id: 41, title: job.title, status: "active", applications_count: 1 }] };
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname;
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!path.startsWith("/api/")) return route.continue();
    if (request.method() !== "GET") calls.push({ path, method: request.method(), body: request.postDataJSON() });
    if (path.endsWith("/admin/stats")) return route.fulfill({ json: { users: 4, candidates: 1, jobs: 1, available_jobs: job.external_available ? 1 : 0 } });
    if (path.endsWith("/admin/jobs/sources/jsearch")) return route.fulfill({ json: { configured: false } });
    if (path.endsWith("/admin/users/11")) return route.fulfill({ json: account });
    if (path.endsWith("/admin/companies/21")) return route.fulfill({ json: company });
    if (path.endsWith("/admin/jobs/41/review")) {
      if (request.method() === "PATCH") {
        if (fail) { fail = false; return route.fulfill({ status: 503, json: { detail: "No se pudo guardar la revisión de ejemplo." } }); }
        const body = request.postDataJSON();
        job = { ...job, moderation_status: body.status, moderation_note: body.note, moderation_revision: 1, external_available: false, history: [{ id: 9, event: "job.publication_reviewed", created_at: "2026-11-03T12:00:00Z", details: { status: body.status } }] };
      }
      return route.fulfill({ json: job });
    }
    if (["/api/v1/admin/users", "/api/v1/admin/companies", "/api/v1/admin/jobs"].includes(path)) return route.fulfill({ json: { items: path.endsWith("users") ? [account] : path.endsWith("companies") ? [company] : [job], total: 1 } });
    if (path.endsWith("/admin/jobs/catalog-status")) return route.fulfill({ json: { running: false } });
    return route.fulfill({ json: {} });
  });
  await page.goto(`/quality/?adminRecords=1&theme=${theme}`);
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Ficha de cuenta", exact: true })).toContainText("Trayectoria registrada");
  await page.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  const nav = page.getByRole("navigation", { name: "Recursos administrativos", exact: true });
  await nav.getByRole("button", { name: /Empresas/ }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Ficha de empresa", exact: true })).toContainText("Vacantes de esta organización");
  await page.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  await nav.getByRole("button", { name: /Vacantes/ }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Revisar vacante", exact: true });
  await expect(dialog.getByText(job.requirements, { exact: true })).toBeVisible();
  await dialog.getByRole("combobox", { name: "Decisión editorial", exact: true }).selectOption("held");
  await dialog.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Revisar las condiciones antes de mostrar la oferta.");
  await dialog.getByRole("button", { name: "Guardar decisión", exact: true }).click();
  await expect(dialog.getByRole("alert")).toContainText("No se pudo guardar");
  await expect(dialog.getByRole("textbox", { name: "Motivo de la decisión", exact: true })).toHaveValue("Revisar las condiciones antes de mostrar la oferta.");
  expect(calls).toHaveLength(1);
  await dialog.getByRole("button", { name: "Guardar decisión", exact: true }).click();
  await expect(dialog.getByRole("status")).toContainText("Decisión editorial guardada");
  expect(calls).toHaveLength(2);
  expect(calls[1].body).toMatchObject({ status: "held", revision: 0 });
  await dialog.locator(".admin-record-history summary").click();
  await expect(dialog.getByText("Revisión editorial", { exact: true })).toBeVisible();
  await dialog.screenshot({ path: `../.local/admin-review-20261103/review-${theme}-${width}.png` });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expect.poll(() => dialog.evaluate((node) => node.scrollWidth - node.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
  expect(calls.every((row) => row.method === "PATCH")).toBe(true);
});

test("Public demonstrations use a numbered profile and show every compatibility change", async ({ page }) => {
  await page.goto("/quality/?entry=1&path=/");
  const progress = page.getByRole("progressbar", { name: "Compatibilidad ilustrativa", exact: true });
  await expect(progress).toHaveAttribute("aria-valuenow", "33");
  await page.getByRole("checkbox", { name: "Análisis de datos", exact: true }).check();
  await expect(progress).toHaveAttribute("aria-valuenow", "67");
  await expect(page.locator(".role-demo-change")).toContainText("+34 puntos");
  await page.getByRole("checkbox", { name: "Comunicación", exact: true }).check();
  await expect(progress).toHaveAttribute("aria-valuenow", "100");
  for (const skill of ["Excel", "Comunicación", "Análisis de datos"]) await page.getByRole("checkbox", { name: skill, exact: true }).uncheck();
  await expect(progress).toHaveAttribute("aria-valuenow", "0");
  await page.getByRole("navigation", { name: "Elige tu espacio", exact: true }).getByRole("link", { name: "Para empresas", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Perfil de ejemplo 01", exact: true })).toBeVisible();
  await expect(page.getByText("Andrea Torres", { exact: true })).toHaveCount(0);
});
