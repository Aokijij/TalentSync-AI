import { test, expect } from "@playwright/test";

const initial = { id: 41, title: "Analista de operaciones", company_id: 21, company_name: "Empresa de revisión", status: "active", source_kind: "external", external_url: "https://example.test/jobs/41", description: "Revisar registros y documentar diferencias para preparar reportes del equipo.", requirements: "Manejo de Excel, comunicación y documentación de procesos.", skills: ["excel", "comunicacion", "documentacion"], quality_details: { contract_type: "fixed_term" }, moderation_revision: 0, moderation_status: "approved", external_check_state: "verified", external_available: true, required_education_level: "secondary", required_study_fields: [], external_content: { education: { status: "required" } }, created_at: "2026-11-04T15:00:00", review: { checks: [] }, history: [] };

async function setup(page, { kind = "external", theme = "light", width = 1280 } = {}) {
  await page.setViewportSize({ width, height: 950 });
  const state = { job: { ...structuredClone(initial), source_kind: kind }, writes: [], fail: false, reads: 0 };
  await page.route("**/api/v1/**", route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (path.endsWith("/admin/jobs/41/review")) { state.reads++; return route.fulfill({ json: state.job }); }
    if (request.method() === "PATCH" && (path.endsWith("/admin/jobs/41/content") || path.endsWith("/jobs/41"))) {
      const payload = request.postDataJSON(); state.writes.push(payload);
      if (state.fail) return route.fulfill({ status: 503, json: { detail: "No se pudo guardar. Conserva los cambios e inténtalo de nuevo." } });
      Object.assign(state.job, payload.fields || payload, { moderation_revision: state.job.moderation_revision + 1 });
      return route.fulfill({ json: state.job });
    }
    if (path.endsWith("/jobs/41")) return route.fulfill({ json: state.job });
    if (path.endsWith("/jobs")) return route.fulfill({ json: request.url().includes("/admin/") ? { items: [state.job], total: 1 } : [state.job] });
    if (path.endsWith("/admin/stats")) return route.fulfill({ json: { jobs: 1 } });
    return route.fulfill({ json: { items: [], total: 0, configured: false } });
  });
  await page.goto(`/quality/?adminRecords=1&theme=${theme}`);
  await page.getByRole("navigation", { name: "Recursos administrativos", exact: true }).getByRole("button", { name: /Vacantes/ }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Revisar vacante", exact: true });
  await dialog.getByRole("button", { name: "Contenido y edición", exact: true }).click();
  await dialog.getByRole("button", { name: "Editar contenido", exact: true }).click();
  return { state, dialog, form: dialog.locator(kind === "external" ? ".external-job-editor" : ".admin-content-editor") };
}

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Protected vacancy editing keeps all sections until save · ${theme} · ${width}`, async ({ page }) => {
  const { state, dialog, form } = await setup(page, { theme, width });
  const text = "Texto actualizado que debe conservarse al cambiar de apartado o intentar salir de la edición.";
  await form.getByRole("textbox", { name: "Funciones y descripción", exact: true }).fill(text);
  await expect(dialog.getByRole("navigation", { name: "Secciones de la ficha" })).toHaveCount(0);
  await expect(dialog.getByRole("link", { name: /Ver vacante completa/ })).toHaveCount(0);
  await expect(form.getByRole("button", { name: /^(Contenido|Condiciones|Requisitos)$/ })).toHaveCount(0);
  await form.getByRole("combobox", { name: "Apartado de edición", exact: true }).selectOption("conditions");
  await form.getByRole("textbox", { name: "Salario mensual publicado en COP", exact: true }).fill("2800000");
  await form.getByRole("combobox", { name: "Apartado de edición", exact: true }).selectOption("requirements");
  await form.getByRole("spinbutton", { name: /Experiencia mínima/ }).fill("6");
  await form.getByRole("combobox", { name: "Apartado de edición", exact: true }).selectOption("content");
  await expect(form.getByRole("textbox", { name: "Funciones y descripción", exact: true })).toHaveValue(text);
  await page.mouse.click(1, 200);
  const alert = page.getByRole("alertdialog", { name: "¿Salir de la edición?", exact: true });
  await expect(alert).toBeVisible();
  await expect(alert.getByRole("button", { name: "Seguir editando", exact: true })).toBeFocused();
  await alert.screenshot({ path: `../.local/protected-editor-20261104/exit-${theme}-${width}.png` });
  await alert.getByRole("button", { name: "Seguir editando", exact: true }).click();
  await expect(form.getByRole("textbox", { name: "Funciones y descripción", exact: true })).toHaveValue(text);
  await page.keyboard.press("Escape");
  await expect(alert).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(alert).toHaveCount(0);
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Cancelar edición", exact: true }).click();
  await expect(alert).toBeVisible();
  await alert.getByRole("button", { name: "Seguir editando", exact: true }).click();
  await form.getByRole("textbox", { name: "Qué información contrastaste en la oferta original", exact: true }).fill("Información contrastada con las condiciones de la oferta original.");
  state.fail = true;
  await form.getByRole("button", { name: "Guardar contenido", exact: true }).click();
  await expect(dialog.getByRole("alert")).toContainText("No se pudo guardar");
  await expect(dialog.getByRole("button", { name: "Actualizar ficha", exact: true })).toHaveCount(0);
  await expect(form.getByRole("textbox", { name: "Funciones y descripción", exact: true })).toHaveValue(text);
  state.fail = false;
  await form.getByRole("button", { name: "Guardar contenido", exact: true }).click();
  await expect(dialog.getByRole("navigation", { name: "Secciones de la ficha" })).toBeVisible();
  expect(state.writes.at(-1).fields.description).toBe(text);
  expect(state.writes.at(-1).fields.salary).toBe(2800000);
  expect(state.writes.at(-1).fields.quality_details.experience_months).toBe(6);
  await dialog.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(alert).toHaveCount(0);
});

test("discard is explicit for close and cancellation, including native offers", async ({ page }) => {
  const { dialog, form, state } = await setup(page, { kind: "internal" });
  await form.getByRole("textbox", { name: "Funciones y descripción", exact: true }).fill("Una edición de una vacante propia que no debe guardarse si se cancela.");
  await dialog.getByRole("button", { name: "Cancelar edición", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Salir sin guardar", exact: true }).click();
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("navigation", { name: "Secciones de la ficha" })).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Editar contenido", exact: true })).toBeVisible();
  expect(state.writes).toHaveLength(0);
  await dialog.getByRole("button", { name: "Editar contenido", exact: true }).click();
  await expect(form.getByRole("textbox", { name: "Funciones y descripción", exact: true })).toHaveValue(initial.description);
  await dialog.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Salir sin guardar", exact: true }).click();
  await expect(dialog).toHaveCount(0);
});

test("refresh warns before leaving an edit and can preserve it", async ({ page }) => {
  const { form } = await setup(page);
  await form.getByRole("textbox", { name: "Funciones y descripción", exact: true }).fill("Cambios locales que deben mantenerse al cancelar la recarga del navegador.");
  let prompted = false;
  page.once("dialog", async dialog => { expect(dialog.type()).toBe("beforeunload"); prompted = true; await dialog.dismiss(); });
  await page.reload({ timeout: 5000 }).catch(() => {});
  expect(prompted).toBe(true);
  await expect(form.getByRole("textbox", { name: "Funciones y descripción", exact: true })).toHaveValue("Cambios locales que deben mantenerse al cancelar la recarga del navegador.");
});

test("vacancy detail describes education as a minimum", async ({ page }) => {
  await setup(page);
  await page.getByRole("dialog").getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Salir sin guardar", exact: true }).click();
  await page.goto("/quality/?entry=1&signed=admin&path=/vacantes/41");
  await expect(page.getByRole("heading", { name: "Formación mínima requerida", exact: true })).toBeVisible();
  await expect(page.getByText(/Bachillerato terminado como nivel mínimo. También se aceptan niveles superiores/)).toBeVisible();
});
