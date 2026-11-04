import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Administrative records support review and editorial decisions · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1050 });
  const calls = [], errors = [];
  let fail = true;
  let job = { id: 41, title: "Analista de datos · Demostración", company_name: "TalentSync · Demostración", company_id: 21, status: "active", source_kind: "external", source_portal: "Portal de ejemplo", external_url: "https://example.test/jobs/41", skills: ["sql", "excel", "python"], salary: 3000000, location: "Medellín", modality: "hybrid", moderation_status: "automatic", moderation_revision: 0, moderation_note: "", external_available: true, external_check_state: "verified", description: "Prepara reportes y revisa la calidad de los datos.", requirements: "Experiencia con consultas SQL y reportes en Excel.", review: { can_publish: true, score: null, checks: [{ label: "Vigencia comprobada", passed: true }] }, history: [] };
  const account = { id: 11, name: "Candidato 01", email: "candidate01@example.test", role: "candidate", profession: "Analista", skills: ["sql"], profile: { profession: "Analista", summary: "Experiencia preparando reportes, revisando registros y documentando resultados para el equipo. Interés en mejorar procesos con análisis de datos.", skills: ["sql"], experiences_count: 2, educations_count: 1, certifications_count: 0, languages: [], has_cv: true }, applications: [{ id: 4, job_id: 41, job_title: job.title, status: "submitted" }] };
  const company = { id: 21, name: "TalentSync", description: "Plataforma que conecta trayectoria profesional, oportunidades y aprendizaje, con herramientas para candidatos y equipos de selección.", mission: "Facilitar procesos de selección claros y el desarrollo de habilidades.", values: ["Claridad", "Colaboración", "Aprendizaje"], location: "Medellín", source_kind: "internal", verification_status: "verified", sector: "Tecnología", jobs_count: 1, jobs: [{ id: 41, title: job.title, status: "active", applications_count: 1 }] };
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
    if (path.endsWith("/admin/jobs/41/content")) {
      const body = request.postDataJSON();
      job = { ...job, ...body.fields, moderation_revision: 2, editorial_overrides: { fields: body.fields, note: body.note, source_url: body.source_url } };
      return route.fulfill({ json: job });
    }
    if (path.endsWith("/admin/jobs/41/catalog-status")) {
      {
        if (fail) { fail = false; return route.fulfill({ status: 503, json: { detail: "No se pudo guardar la revisión de ejemplo." } }); }
        const body = request.postDataJSON();
        job = { ...job, status: body.status, moderation_status: "held", moderation_note: body.note, moderation_revision: 1, external_available: false, history: [{ id: 9, event: "job.status_updated", created_at: "2026-11-03T12:00:00Z", details: { status: body.status } }] };
      }
      return route.fulfill({ json: job });
    }
    if (path.endsWith("/admin/jobs/41/review")) return route.fulfill({ json: job });
    if (["/api/v1/admin/users", "/api/v1/admin/companies", "/api/v1/admin/jobs"].includes(path)) return route.fulfill({ json: { items: path.endsWith("users") ? [account] : path.endsWith("companies") ? [company] : [job], total: 1 } });
    if (path.endsWith("/admin/jobs/catalog-status")) return route.fulfill({ json: { running: false } });
    return route.fulfill({ json: {} });
  });
  await page.goto(`/quality/?adminRecords=1&theme=${theme}`);
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Ficha de cuenta", exact: true })).toContainText("Trayectoria registrada");
  await page.getByRole("dialog").screenshot({ path: `../.local/platform-polish-20261104/account-${theme}-${width}.png` });
  await page.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  const nav = page.getByRole("navigation", { name: "Recursos administrativos", exact: true });
  await nav.getByRole("button", { name: /Empresas/ }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  await page.getByRole("dialog").screenshot({ path: `../.local/platform-polish-20261104/company-${theme}-${width}.png` });
  await page.getByRole("dialog", { name: "Ficha de empresa", exact: true }).getByRole("button", { name: "Vacantes", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Ficha de empresa", exact: true })).toContainText("Vacantes de esta organización");
  await page.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  await nav.getByRole("button", { name: /Vacantes/ }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Revisar vacante", exact: true });
  await expect(dialog.getByText(job.requirements, { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Publicación", exact: true }).click();
  await dialog.getByRole("combobox", { name: "Estado en TalentSync", exact: true }).selectOption("paused");
  await dialog.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Revisar las condiciones antes de mostrar la oferta.");
  await dialog.getByRole("button", { name: "Guardar estado", exact: true }).click();
  await expect(dialog.getByRole("alert")).toContainText("No se pudo guardar");
  await expect(dialog.getByRole("textbox", { name: "Motivo de la decisión", exact: true })).toHaveValue("Revisar las condiciones antes de mostrar la oferta.");
  expect(calls).toHaveLength(1);
  await dialog.getByRole("button", { name: "Guardar estado", exact: true }).click();
  await expect(dialog.getByRole("status")).toContainText("Estado de la vacante actualizado");
  expect(calls).toHaveLength(2);
  expect(calls[1].body).toMatchObject({ status: "paused", revision: 0 });
  await dialog.screenshot({ path: `../.local/platform-polish-20261104/publication-${theme}-${width}.png` });
  await dialog.getByRole("button", { name: "Historial", exact: true }).click();
  await expect(dialog.getByText("Cambio de estado", { exact: true })).toBeVisible();
  await dialog.screenshot({ path: `../.local/admin-review-20261103/review-${theme}-${width}.png` });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expect.poll(() => dialog.evaluate((node) => node.scrollWidth - node.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
  expect(calls.every((row) => row.method === "PATCH")).toBe(true);
  await page.evaluate(() => { document.documentElement.style.fontSize = ""; });
  await dialog.getByRole("button", { name: "Contenido y edición", exact: true }).click();
  await dialog.getByRole("button", { name: "Editar contenido", exact: true }).click();
  await dialog.getByRole("textbox", { name: "Funciones y descripción", exact: true }).fill("Funciones ampliadas desde la fuente original: preparar reportes y revisar la calidad de las consultas SQL.");
  await dialog.getByRole("textbox", { name: "Qué información contrastaste en la oferta original" }).fill("Funciones contrastadas con el texto completo del portal original.");
  await dialog.getByRole("button", { name: "Guardar contenido", exact: true }).click();
  await expect(dialog.getByRole("status")).toContainText("Contenido actualizado");
  expect(calls[2].body.revision).toBe(1);
  expect(calls[2].body.fields.description).toContain("Funciones ampliadas");
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

test("Internal workspaces appear in verification with an operational decision", async ({ page }) => {
  const writes = [];
  const organization = { id: 21, name: "TalentSync", nit: "TALENTSYNC-INTERNA", verification_kind: "internal", status: "reviewing", email_verified: true, verification_missing: [], submission: { kind: "internal", submitted_at: "2026-11-04", platform_url: "https://example.test", responsible_name: "Equipo de ejemplo", business_activity: "Operación de la plataforma" } };
  await page.route("**/api/v1/**", route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (path.endsWith("/admin/verification-queue")) return route.fulfill({ json: { items: [organization], total: 1, page: 1, counts: { reviewing: 1 } } });
    if (path.endsWith("/admin/verifications/21")) { writes.push(request.postDataJSON()); return route.fulfill({ json: {} }); }
    return route.fulfill({ json: { count: 0 } });
  });
  await page.goto("/quality/?entry=1&signed=admin&path=/admin/verificaciones");
  await expect(page.getByRole("heading", { name: "TalentSync", exact: true })).toBeVisible();
  await expect(page.getByText(/Identificación interna: TALENTSYNC-INTERNA/)).toBeVisible();
  await page.getByText("Revisar soportes y registrar una decisión", { exact: true }).click();
  await expect(page.getByRole("option", { name: "Aprobar verificación legal", exact: true })).toHaveCount(0);
  await page.getByRole("combobox", { name: "Nueva decisión", exact: true }).selectOption("internal_approved");
  await page.getByRole("textbox", { name: "Motivo que recibirá la empresa", exact: true }).fill("Revisado el enlace y el responsable del espacio interno de la plataforma.");
  await page.getByRole("button", { name: "Guardar revisión", exact: true }).click();
  expect(writes).toHaveLength(0);
  await page.getByRole("alertdialog").getByRole("button", { name: "Guardar decisión", exact: true }).click();
  await expect.poll(() => writes.length).toBe(1);
  expect(writes[0].status).toBe("internal_approved");
});

test("Catalogue cleanup is separate, starts unselected and requires a concrete confirmation", async ({ page }) => {
  let writes = 0;
  await page.route("**/api/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/admin/jobs/cleanup")) {
      if (route.request().method() === "POST") { writes += 1; expect(route.request().postDataJSON().ids).toEqual([41]); return route.fulfill({ json: { deleted: 1, skipped: [] } }); }
      return route.fulfill({ json: { total: writes ? 0 : 1, items: writes ? [] : [{ id: 41, title: "Oferta vencida de ejemplo", company_name: "Empresa de ejemplo", reason: "expired" }], protected: "Los fallos temporales se conservan." } });
    }
    if (path.endsWith("/admin/stats")) return route.fulfill({ json: {} });
    return route.fulfill({ json: { items: [], total: 0 } });
  });
  await page.goto("/quality/?adminRecords=1");
  await page.getByRole("navigation", { name: "Recursos administrativos", exact: true }).getByRole("button", { name: /Vacantes/ }).click();
  await expect(page.getByRole("heading", { name: "Más oportunidades, con información útil", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Limpieza", exact: true }).click();
  await expect(page.getByRole("button", { name: "Eliminar seleccionadas (0)", exact: true })).toBeDisabled();
  await page.getByRole("checkbox", { name: /Oferta vencida de ejemplo/ }).check();
  await page.getByRole("button", { name: "Eliminar seleccionadas (1)", exact: true }).click();
  expect(writes).toBe(0);
  await page.getByRole("alertdialog").getByRole("button", { name: "Eliminar seleccionadas", exact: true }).click();
  await expect(page.getByText("1 ofertas eliminadas. 0 se conservaron al volver a comprobarlas.", { exact: true })).toBeVisible();
  expect(writes).toBe(1);
});
