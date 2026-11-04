import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`External offer partial edits, re-edit, check and publication · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  const writes = [], errors = [];
  let verified = false, complete = false;
  let job = { id: 41, title: "Analista de datos", company_id: 21, company_name: "Empresa de ejemplo", status: "active", source_kind: "external", source_portal: "Portal original", external_url: "https://example.test/jobs/41", description: "Extracción parcial", requirements: "Parcial", skills: ["sql", "python", "excel"], languages: [], benefits: [], salary: null, modality: "remote", employment_type: "full_time", required_study_fields: [], quality_details: {}, moderation_status: "automatic", moderation_revision: 0, external_check_state: "unknown", external_available: false };
  const detail = () => ({ ...job, external_available: verified && complete && job.moderation_status !== "held", review: { can_publish: verified && complete && job.status === "active", can_activate: verified && complete, checks: [{ label: "Estado en el catálogo", passed: job.status === "active" }, { label: "Vigencia confirmada recientemente", passed: verified }, { label: "Contenido suficiente", passed: complete }] }, history: [] });
  page.on("pageerror", error => errors.push(error.message));
  await page.route("**/api/v1/**", route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (path.endsWith("/admin/jobs/41/review")) return route.fulfill({ json: detail() });
    if (path.endsWith("/admin/jobs/41/content")) {
      const body = request.postDataJSON(); writes.push({ path, body });
      expect(body.revision).toBe(job.moderation_revision);
      const fields = body.fields, quality = { ...job.quality_details, ...fields.quality_details };
      job = { ...job, ...fields, quality_details: quality, moderation_revision: job.moderation_revision + 1 };
      if (fields.description && fields.requirements) complete = true;
      return route.fulfill({ json: detail() });
    }
    if (path.endsWith("/admin/jobs/41/availability/check")) { verified = true; job.external_check_state = "verified"; return route.fulfill({ json: { state: "verified", available: complete, checked_at: "2026-11-04T12:00:00Z" } }); }
    if (path.endsWith("/admin/jobs/41/catalog-status")) {
      const body = request.postDataJSON(); writes.push({ path, body }); expect(body.revision).toBe(job.moderation_revision);
      expect(verified && complete).toBe(true);
      job = { ...job, status: body.status, moderation_status: body.status === "active" ? "approved" : "held", moderation_revision: job.moderation_revision + 1 };
      return route.fulfill({ json: detail() });
    }
    if (path.endsWith("/admin/stats")) return route.fulfill({ json: { jobs: 1 } });
    return route.fulfill({ json: { items: [detail()], total: 1, configured: false } });
  });
  await page.goto(`/quality/?adminRecords=1&theme=${theme}`);
  await page.getByRole("navigation", { name: "Recursos administrativos", exact: true }).getByRole("button", { name: /Vacantes/ }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Revisar vacante", exact: true });
  await dialog.getByRole("button", { name: "Contenido y edición", exact: true }).click();
  await dialog.getByRole("button", { name: "Editar contenido", exact: true }).click();
  const form = dialog.locator(".external-job-editor");
  await form.getByRole("button", { name: "Requisitos", exact: true }).click();
  await form.getByRole("spinbutton", { name: /Experiencia mínima/ }).fill("24");
  await form.getByRole("button", { name: /^Añadir idioma/ }).click();
  await form.getByRole("combobox", { name: "Idioma 1", exact: true }).fill("inglés");
  await form.getByRole("option", { name: "inglés", exact: true }).click();
  await form.getByRole("combobox", { name: "Nivel del idioma 1", exact: true }).click();
  await form.getByRole("option", { name: "B2 · Intermedio alto", exact: true }).click();
  await form.getByRole("button", { name: "Condiciones", exact: true }).click();
  expect(errors).toEqual([]);
  await form.getByRole("textbox", { name: "Salario mensual publicado en COP", exact: true }).fill("3200000");
  await expect(form.getByRole("textbox", { name: "Salario mensual publicado en COP", exact: true })).toHaveValue("3.200.000");
  await form.getByRole("combobox", { name: "Modalidad", exact: true }).selectOption("hybrid");
  await form.getByRole("button", { name: "Escribir horario", exact: true }).click();
  await form.getByRole("textbox", { name: "Describe la jornada", exact: true }).fill("Lunes a viernes de 08:00 a 17:00, con una hora de descanso.");
  await form.getByRole("textbox", { name: "Qué información contrastaste en la oferta original", exact: true }).fill("Experiencia, idioma y condiciones contrastados en la oferta original.");
  await dialog.locator(".admin-record-body").evaluate(node => { node.scrollTop = 0; });
  await dialog.screenshot({ path: `../.local/external-editor-20261104/editor-${theme}-${width}.png` });
  await form.getByRole("button", { name: "Guardar contenido", exact: true }).click();
  await expect(dialog.getByRole("status")).toContainText("Contenido actualizado");
  expect(writes[0].body.fields).not.toHaveProperty("description");
  expect(writes[0].body.fields.quality_details.experience_months).toBe(24);
  expect(writes[0].body.fields.languages).toEqual([{ name: "inglés", level: "B2" }]);
  await dialog.getByRole("button", { name: "Editar contenido", exact: true }).click();
  await form.getByRole("textbox", { name: "Funciones y descripción", exact: true }).fill("Preparar reportes de seguimiento y contrastar los registros del equipo. Documentar diferencias y comunicar resultados.");
  await form.getByRole("textbox", { name: "Requisitos de la oferta", exact: true }).fill("Manejo de SQL, Python y Excel para revisar los registros y preparar reportes del equipo.");
  await form.getByRole("button", { name: "Condiciones", exact: true }).click();
  await expect(form.getByRole("textbox", { name: "Salario mensual publicado en COP", exact: true })).toHaveValue("3.200.000");
  await expect(form.getByRole("combobox", { name: "Modalidad", exact: true })).toHaveValue("hybrid");
  await form.getByRole("textbox", { name: "Qué información contrastaste en la oferta original", exact: true }).fill("Se completaron las funciones y requisitos desde el portal original.");
  await form.getByRole("button", { name: "Guardar contenido", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "Editar contenido", exact: true })).toBeEnabled();
  await dialog.getByRole("button", { name: "Publicación", exact: true }).click();
  await dialog.getByRole("button", { name: "Comprobar fuente", exact: true }).click();
  await expect(dialog.getByText("Cumple los controles", { exact: true })).toBeVisible();
  for (const [status, button] of [["active", "Publicar vacante"], ["paused", "Guardar estado"], ["active", "Publicar vacante"]]) {
    await dialog.getByRole("combobox", { name: "Estado en TalentSync", exact: true }).selectOption(status);
    await dialog.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Revisión de contenido y condiciones completada en el portal original.");
    await dialog.getByRole("button", { name: button, exact: true }).click();
    await expect(dialog.getByRole("status")).toContainText("Estado de la vacante actualizado");
    await expect(dialog.getByRole("textbox", { name: "Motivo de la decisión", exact: true })).toHaveValue("");
  }
  expect(writes.map(row => row.body.revision)).toEqual([0, 1, 2, 3, 4]);
  await page.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  await dialog.getByRole("button", { name: "Contenido y edición", exact: true }).click();
  await dialog.getByRole("button", { name: "Editar contenido", exact: true }).click();
  await form.getByRole("button", { name: "Requisitos", exact: true }).click();
  await expect(form.getByRole("spinbutton", { name: /Experiencia mínima/ })).toHaveValue("24");
  await expect(form.getByRole("combobox", { name: "Idioma 1", exact: true })).toHaveValue("inglés");
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  for (const name of ["Contenido", "Condiciones", "Requisitos"]) {
    await form.getByRole("button", { name, exact: true }).click();
    expect(await dialog.evaluate(node => node.scrollWidth - node.clientWidth), name).toBeLessThanOrEqual(1);
  }
  expect(errors).toEqual([]);
});
