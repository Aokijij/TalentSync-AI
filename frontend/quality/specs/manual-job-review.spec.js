import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Manual source review requires an explicit decision · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  let write;
  let job = { id: 41, title: "Analista de datos", company_id: 21, company_name: "Empresa de ejemplo", status: "active", source_kind: "external", external_url: "https://example.test/jobs/41", description: "Preparar reportes y documentar diferencias de los registros.", requirements: "Conocimientos de Python, SQL y Excel para analizar registros.", skills: ["sql", "python", "excel"], quality_details: { contract_type: "fixed_term" }, moderation_revision: 0, moderation_status: "automatic", external_check_state: "unknown", external_available: false, review: { checks: [{ label: "Estado", passed: true }, { label: "Vigencia confirmada recientemente", passed: false }] }, history: [] };
  await page.route("**/api/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/admin/jobs/41/review")) return route.fulfill({ json: job });
    if (path.endsWith("/admin/jobs/41/catalog-status")) {
      write = route.request().postDataJSON();
      job = { ...job, external_available: true, external_verification_method: "manual", external_manual_verified_at: "2026-11-04T15:00:00", external_manual_verified_until: "2026-11-07T15:00:00", moderation_revision: 1, review: { checks: [{ label: "Estado", passed: true }, { label: "Vigencia confirmada recientemente", passed: true }] } };
      return route.fulfill({ json: job });
    }
    if (path.endsWith("/admin/stats")) return route.fulfill({ json: { jobs: 1 } });
    return route.fulfill({ json: { items: [job], total: 1, configured: false } });
  });
  await page.goto(`/quality/?adminRecords=1&theme=${theme}`);
  await page.getByRole("navigation", { name: "Recursos administrativos", exact: true }).getByRole("button", { name: /Vacantes/ }).click();
  await page.getByRole("button", { name: "Ver ficha", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Revisar vacante", exact: true });
  await dialog.getByRole("button", { name: "Publicación", exact: true }).click();
  const confirmation = dialog.getByRole("checkbox", { name: /He abierto la oferta original/ });
  await expect(confirmation).not.toBeChecked();
  await expect(dialog.getByRole("link", { name: /Abrir oferta original/ })).toHaveAttribute("href", job.external_url);
  await confirmation.check();
  await dialog.getByRole("textbox", { name: "Motivo de la decisión", exact: true }).fill("Revisé la oferta original y su formulario sigue recibiendo postulaciones.");
  await dialog.locator(".publication-manual-review").screenshot({ path: `../.local/manual-review-20261104/manual-${theme}-${width}.png` });
  expect(await dialog.evaluate(node => node.scrollWidth - node.clientWidth)).toBeLessThanOrEqual(1);
  await dialog.getByRole("button", { name: "Publicar vacante", exact: true }).click();
  await expect(dialog.getByRole("status").filter({ hasText: "Estado de la vacante actualizado" })).toBeVisible();
  expect(write.manual_verification).toEqual({ confirmed_open: true, source_url: job.external_url, note: write.note });
  await expect(confirmation).not.toBeChecked();
  await expect(dialog.getByText("Revisada por administración", { exact: true })).toBeVisible();
  await expect(dialog.getByRole("link", { name: /Ver vacante completa/ })).toHaveAttribute("href", "/vacantes/41");
});

test("saved contract updates an already open vacancy in another tab", async ({ context, page }) => {
  let job = { id: 41, title: "Analista de datos", company_id: 21, company_name: "Empresa de ejemplo", status: "active", source_kind: "external", external_url: "https://example.test/jobs/41", created_at: "2026-11-04T12:00:00", description: "Preparar reportes y documentar diferencias.", requirements: "Python, SQL y Excel", skills: ["sql", "python", "excel"], quality_details: {}, moderation_revision: 0, moderation_status: "approved", external_available: true, external_check_state: "verified", review: { checks: [] }, history: [] };
  await context.route("**/api/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/admin/jobs/41/content")) {
      const fields = route.request().postDataJSON().fields;
      job = { ...job, ...fields, quality_details: { ...job.quality_details, ...fields.quality_details }, moderation_revision: 1 };
      return route.fulfill({ json: job });
    }
    if (path.endsWith("/jobs/41") || path.endsWith("/admin/jobs/41/review")) return route.fulfill({ json: job });
    if (path.endsWith("/admin/stats")) return route.fulfill({ json: { jobs: 1 } });
    if (path.endsWith("/admin/jobs")) return route.fulfill({ json: { items: [job], total: 1 } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/quality/?entry=1&signed=admin&path=/vacantes/41");
  await expect(page.getByText("Tipo de contrato no especificado", { exact: true })).toBeVisible();
  const editor = await context.newPage();
  await editor.goto("/quality/?adminRecords=1");
  await editor.getByRole("navigation", { name: "Recursos administrativos", exact: true }).getByRole("button", { name: /Vacantes/ }).click();
  await editor.getByRole("button", { name: "Ver ficha", exact: true }).click();
  const dialog = editor.getByRole("dialog", { name: "Revisar vacante", exact: true });
  await dialog.getByRole("button", { name: "Contenido y edición", exact: true }).click();
  await dialog.getByRole("button", { name: "Editar contenido", exact: true }).click();
  await dialog.getByRole("combobox", { name: "Apartado de edición", exact: true }).selectOption("conditions");
  await dialog.getByRole("combobox", { name: /Tipo de contrato/ }).selectOption("fixed_term");
  await dialog.getByRole("textbox", { name: "Qué información contrastaste en la oferta original", exact: true }).fill("Contrato a término fijo contrastado en la fuente original.");
  await dialog.getByRole("button", { name: "Guardar contenido", exact: true }).click();
  await expect(page.getByText("Tipo de contrato no especificado", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Término fijo", { exact: true })).toHaveCount(2);
  await page.locator(".external-review-banner").screenshot({ path: "../.local/manual-review-20261104/banner-light.png" });
});
