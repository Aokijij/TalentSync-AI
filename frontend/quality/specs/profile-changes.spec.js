import { test, expect } from "@playwright/test";
for (const width of [360, 1440]) test(`Profile keeps edits after failed save and confirms discard · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 950 });
  let allowSave = false, writes = 0;
  let profile = { profession: "Analista de datos", location: "Medellín", department: "Antioquia", phone: "3000000000", skills: ["excel"], experiences: [], educations: [], certifications: [], languages: [], preferences: {}, summary: "Organizo información para apoyar al equipo.", mobility: {}, availability: "immediate" };
  const errors = []; page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (url.hostname !== "127.0.0.1" || url.pathname.startsWith("/api/") && !["/api/v1/profiles/me", "/api/v1/auth/me", "/api/v1/matching/evidence"].includes(url.pathname)) return route.abort();
    if (url.pathname.endsWith("/auth/me")) return route.fulfill({ json: { id: 1, name: "Persona de ejemplo", email: "example@example.test", role: "candidate" } });
    if (url.pathname.endsWith("/matching/evidence")) return route.fulfill({ json: [] });
    if (url.pathname.endsWith("/profiles/me")) {
      if (route.request().method() === "PUT") {
        writes++;
        if (!allowSave) return route.fulfill({ status: 503, json: { detail: "No pudimos guardar el perfil de ejemplo. Inténtalo de nuevo." } });
        profile = { ...profile, ...route.request().postDataJSON() };
      }
      return route.fulfill({ json: profile });
    }
    return route.continue();
  });
  await page.goto(`/quality/?profile=1&theme=${width === 360 ? "light" : "dark"}`);
  await page.getByRole("button", { name: "Editar perfil", exact: true }).click();
  const profession = page.getByRole("textbox", { name: "Título profesional", exact: true });
  await profession.fill("Analista de operaciones");
  await expect(page.getByText("Tienes cambios sin guardar", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Cancelar edición", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Seguir editando", exact: true }).click();
  await expect(profession).toHaveValue("Analista de operaciones");
  await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "No pudimos guardar el perfil de ejemplo" })).toBeVisible();
  await expect(profession).toHaveValue("Analista de operaciones");
  expect(writes).toBe(1);
  await page.getByRole("button", { name: "Cancelar edición", exact: true }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Descartar cambios", exact: true }).click();
  await expect(profession).toHaveCount(0);
  await expect(page.getByText("Analista de datos", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Editar perfil", exact: true }).click();
  await profession.fill("Analista de operaciones"); allowSave = true;
  await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
  await expect(page.getByText("Hoja de vida actualizada correctamente", { exact: true })).toBeVisible();
  await expect(page.getByText("Tienes cambios sin guardar", { exact: true })).toHaveCount(0);
  expect(writes).toBe(2); expect(errors).toEqual([]);
});
