import { test, expect } from "@playwright/test";

const ready = { score: 100, level: "A", can_publish: true, rating: { code: "A", label: "Excelente" } };
const offer = id => ({ id, company_id: 98, company_name: "Equipo de producto", title: `Desarrollo de producto ${id}`, description: "Construir mejoras de la plataforma, comprobar su accesibilidad y documentar los resultados con el equipo.", requirements: "Conocimientos de React, JavaScript y comunicación de decisiones.", source_kind: "internal", status: "draft", sector: "Tecnologia y software", location: "Colombia", modality: "remote", skills: ["react", "javascript", "comunicacion"], salary: 3200000, employment_type: "full_time", quality_revision: 2, quality_summary: ready, quality_details: { salary_max: 3800000, salary_currency: "COP", salary_period: "monthly", salary_basis: "gross_base", contract_type: "indefinite", seniority: "junior", experience_months: 0, schedule: "Lunes a viernes de 08:00 a 17:00", weekly_hours: 40, learnable_skills: ["testing"], missions: [30, 60, 90].map(days => ({ days, outcome: `Entregar una mejora verificable del producto a los ${days} días.`, measure: "Revisión del entregable y pruebas acordadas con el equipo.", skill: "react" })), process_days: 14, interview_count: 2 }, pipeline_stages: [{ id: "submitted", title: "Postulación recibida" }, { id: "reviewing", title: "Revisión de trayectoria" }, { id: "interview", title: "Entrevista de equipo" }, { id: "hired", title: "Selección confirmada" }, { id: "rejected", title: "Cierre con respuesta" }], created_at: "2026-11-04T15:00:00", applications_count: 0 });

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Company vacancy states, quality and preview · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  await page.addInitScript(value => localStorage.setItem("talentsync_theme", value), theme);
  const errors = [], writes = [];
  page.on("pageerror", error => errors.push(error.message));
  const jobs = [1, 2, 3, 4, 5, 6, 7, 8].map(offer);
  jobs[0].status = "active";
  jobs[1].quality_summary = { score: 38, level: "Pendiente", can_publish: false }; jobs[1].title = "Diseño por completar";
  jobs[6].status = "closed"; jobs[6].title = "Revisión cerrada";
  jobs[7].company_id = 200;
  await page.route("**/api/v1/**", route => {
    const request = route.request(), path = new URL(request.url()).pathname.replace("/api/v1", "");
    if (path === "/jobs") return route.fulfill({ json: jobs });
    if (path === "/companies/me" || path === "/organization/me") return route.fulfill({ json: { id: 98, name: "Equipo de producto", role: "owner", active: true, verification_required: false, verification_status: "internal_approved" } });
    if (/^\/jobs\/\d+$/.test(path)) {
      const job = jobs.find(row => row.id === Number(path.split("/").at(-1)));
      if (request.method() === "PATCH") { writes.push(request.postDataJSON()); Object.assign(job, request.postDataJSON()); }
      return route.fulfill({ json: job });
    }
    if (path === "/notifications/unread-count") return route.fulfill({ json: { count: 0 } });
    return route.fulfill({ json: [] });
  });
  await page.goto(`/quality/?entry=1&signed=company&path=/empresa/vacantes&theme=${theme}`);
  await expect(page.getByRole("heading", { name: "Vacantes de Equipo de producto" })).toBeVisible();
  await expect(page.getByText("4 borradores con contenido listo · 1 por completar", { exact: true })).toBeVisible();
  await page.screenshot({ path: `../.local/vacancies-platform-20261104/panel-${theme}-${width}.png` });
  await page.getByRole("combobox", { name: "Estado de las vacantes" }).selectOption("draft");
  await page.getByRole("combobox", { name: "Contenido de la oferta" }).selectOption("incomplete");
  const incomplete = page.locator(".company-vacancy-card");
  await expect(incomplete).toHaveCount(1);
  await expect(incomplete.getByRole("button", { name: "Publicar", exact: true })).toBeDisabled();
  await expect(incomplete.getByRole("button", { name: "Editar borrador", exact: true })).toBeEnabled();
  await page.getByRole("combobox", { name: "Contenido de la oferta" }).selectOption("all");
  await page.getByRole("combobox", { name: "Estado de las vacantes" }).selectOption("closed");
  await expect(page.locator(".company-vacancy-card")).toHaveCount(1);
  await expect(page.locator(".company-vacancy-card").getByText("Cerrada", { exact: true })).toBeVisible();
  await page.getByRole("combobox", { name: "Estado de las vacantes" }).selectOption("active");
  await expect(page.getByRole("link", { name: "Ver vacante completa", exact: true })).toHaveAttribute("href", "/vacantes/1");
  await page.getByRole("button", { name: "Pausar", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Vacante pausada" })).toBeVisible();
  expect(writes).toEqual([{ status: "paused" }]);
  await page.goto(`/quality/?entry=1&signed=company&path=/vacantes/3&theme=${theme}`);
  await expect(page.getByText("Borrador · Vista previa del equipo", { exact: true })).toBeVisible();
  await expect(page.getByRole("list", { name: "Etapas de selección" }).getByRole("listitem")).toHaveCount(3);
  await expect(page.getByText("Posibles resultados: Selección confirmada o Cierre con respuesta.", { exact: true })).toBeVisible();
  await page.locator(".offer-conditions").screenshot({ path: `../.local/vacancies-platform-20261104/conditions-${theme}-${width}.png` });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  expect(await page.locator(".job-detail-page").evaluate(node => node.scrollWidth - node.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});
