import { test, expect } from "@playwright/test";

for (const width of [360, 1280]) for (const theme of ["light", "dark"]) test(`Response commitment and pause · ${width} · ${theme}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1050 });
  const errors = [], writes = []; let fail = true;
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    if (request.url().endsWith("/deadline-extension")) {
      const data = request.postDataJSON(); writes.push(data);
      if (fail) { fail = false; return route.fulfill({ status: 503, json: { detail: "No pudimos guardar el compromiso. Inténtalo de nuevo." } }); }
      return route.fulfill({ json: { application_id: 101, job_id: 101, company_name: "Empresa de ejemplo", candidate_name: "Persona de ejemplo", status: "reviewing", stage: "reviewing", stage_title: "En revisión", created_at: "2020-10-10T15:00:00", response_days: 5, version: 4, can_manage: true, response_due_at: data.due_at, response_state: "on_time", response_paused_at: null, deadline_extension_count: 1,
        events: [{ id: 2, type: "application.deadline_extended", source: "company", resumed: true, extension_reason: data.reason, deadline: data.due_at, at: new Date().toISOString() }] } });
    }
    return route.fulfill({ status: 404, json: { detail: "Ruta inesperada" } });
  });
  await page.goto(`/quality/?deadlines=1&role=company&theme=${theme}`);
  await expect(page.getByRole("heading", { name: "En revisión", exact: true })).toBeVisible();
  await expect(page.getByText("En pausa · Falta de respuesta de la empresa", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Reanudar con nuevo plazo", exact: true }).click();
  await page.getByLabel("Motivo que recibirá el candidato").fill("El equipo necesita contrastar las evidencias antes de comunicar una decisión.");
  await page.getByRole("button", { name: "Revisar ampliación", exact: true }).click();
  const confirmation = page.getByRole("alertdialog", { name: "Reanudar con un nuevo compromiso", exact: true });
  await confirmation.getByRole("button", { name: "Cancelar", exact: true }).click();
  expect(writes).toHaveLength(0);
  await page.getByRole("button", { name: "Revisar ampliación", exact: true }).click();
  await confirmation.getByRole("button", { name: "Confirmar y avisar", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("No pudimos guardar");
  await expect(page.getByLabel("Motivo que recibirá el candidato")).toHaveValue(/El equipo necesita/);
  await page.screenshot({ path: `../.local/response-followup-review/extension-${theme}-${width}.png`, fullPage: true });
  await page.getByRole("button", { name: "Revisar ampliación", exact: true }).click();
  await confirmation.getByRole("button", { name: "Confirmar y avisar", exact: true }).click();
  await expect(page.getByText("Respuesta comprometida", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ampliar plazo", exact: true })).toHaveCount(0);
  expect(writes[1].expected_version).toBe(3);
  await page.getByRole("tab", { name: "Historial", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Proceso retomado con nuevo compromiso", exact: true })).toBeVisible();
  await expect(page.getByText(writes[1].reason, { exact: false })).toBeVisible();
  await page.goto(`/quality/?deadlines=1&role=candidate&theme=${theme}`);
  await expect(page.getByText("En pausa · Falta de respuesta de la empresa", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Ampliar plazo|Reanudar con nuevo plazo/ })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "En revisión", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Ver mis postulaciones", exact: true })).toHaveAttribute("href", "/postulaciones?focus=101");
  await page.screenshot({ path: `../.local/response-followup-review/candidate-${theme}-${width}.png`, fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});
