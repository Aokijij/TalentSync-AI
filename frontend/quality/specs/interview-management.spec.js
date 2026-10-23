import { test, expect } from "@playwright/test";

for (const width of [360, 1280]) for (const theme of ["light", "dark"]) test(`Interview management · ${width} · ${theme}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 950 });
  const errors = [], saved = []; let reject = true;
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (path.endsWith("/applications/101/status")) {
      const payload = request.postDataJSON(); saved.push(payload);
      if (reject) { reject = false; return route.fulfill({ status: 409, json: { detail: "No se pudo guardar la entrevista. Inténtalo de nuevo." } }); }
      return route.fulfill({ json: { ...payload, id: 101, version: saved.length } });
    }
    if (path.endsWith("/calendar")) return route.fulfill({ json: { state: "none", minutes: 60 } });
    return route.fulfill({ status: 404, json: { detail: "Ruta inesperada" } });
  });
  await page.goto(`/quality/?interviews=1&role=company&theme=${theme}`);
  await page.getByRole("button", { name: /Gestionar entrevistas/ }).click();
  await page.getByRole("button", { name: "Gestionar entrevista", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Candidata de ejemplo", exact: true });
  await dialog.getByRole("button", { name: /^Fecha / }).click();
  await dialog.getByRole("button", { name: "31 de octubre de 2030", exact: true }).click();
  await dialog.getByRole("button", { name: /^Hora / }).click();
  const time = page.getByRole("dialog", { name: "Seleccionar hora", exact: true });
  await time.getByRole("group", { name: "Horas", exact: true }).getByRole("button", { name: "10", exact: true }).click();
  await time.getByRole("group", { name: "Minutos", exact: true }).getByRole("button", { name: "30", exact: true }).click();
  await dialog.getByRole("combobox", { name: "Modalidad", exact: true }).selectOption("in_person");
  await dialog.getByLabel("Dirección de la entrevista").fill("Medellín, Calle 10 # 20-30, oficina 4");
  await dialog.getByRole("combobox", { name: "Duración", exact: true }).selectOption("90");
  await dialog.getByLabel("Indicaciones para el candidato (opcional)").fill("Trae un ejemplo de tu proyecto.");
  await dialog.getByRole("button", { name: "Guardar y notificar", exact: true }).click();
  await expect(dialog.getByRole("alert")).toContainText("No se pudo guardar");
  await expect(dialog.getByLabel("Dirección de la entrevista")).toHaveValue("Medellín, Calle 10 # 20-30, oficina 4");
  await page.screenshot({ path: `../.local/interview-review/dialog-${theme}-${width}.png`, fullPage: true });
  await dialog.getByRole("button", { name: "Guardar y notificar", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  expect(saved[1].interview_details).toEqual({ mode: "in_person", minutes: 90, location: "Medellín, Calle 10 # 20-30, oficina 4", instructions: "Trae un ejemplo de tu proyecto." });
  expect(saved[1].interview_at).toBe("2030-10-31T15:30:00.000Z");
  await expect(page.getByText("Presencial · 90 min").first()).toBeVisible();
  await page.screenshot({ path: `../.local/interview-review/agenda-${theme}-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: "Gestionar entrevista", exact: true }).click();
  await dialog.getByRole("button", { name: "Cancelar esta entrevista", exact: true }).click();
  await dialog.getByRole("button", { name: "Guardar y notificar", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  expect(saved.at(-1).interview_at).toBeNull();
  expect(saved.at(-1).interview_details).toBeNull();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});
