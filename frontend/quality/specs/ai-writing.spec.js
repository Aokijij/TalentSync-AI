import { test, expect } from "@playwright/test";

const service = { provider: "groq", name: "Groq", external: true, available: true, summary_available: true };

async function setup(page, { width = 360, theme = "dark", available = true } = {}) {
  await page.setViewportSize({ width, height: 950 });
  const calls = [], errors = [];
  let profile = { profession: "Analista de datos", experience: "Apoyo en la actualización de registros con Excel.", summary_mode: "custom", location: "Medellín", skills: ["excel"], experiences: [{ role: "Analista", company: "Organización de ejemplo", description: "Apoyo en actualización de registros con Excel", start_date: "2020-01", end_date: "2022-01" }, { role: "Asesor", company: "Otro equipo", description: "Atención a clientes", start_date: "2018-01", end_date: "2019-01" }], educations: [], certifications: [], languages: [], preferences: {}, mobility: {} };
  const writing = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname;
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!path.startsWith("/api/")) return route.continue();
    if (request.method() !== "GET") calls.push({ path, body: request.postDataJSON() });
    if (path.endsWith("/auth/me")) return route.fulfill({ json: { id: 1, name: "Persona de ejemplo", role: "candidate", email: "example@example.test" } });
    if (path.endsWith("/writing-service")) return route.fulfill({ json: { ...service, available, summary_available: available } });
    if (path.endsWith("/summary/generate")) return route.fulfill({ json: { text: "Soy analista de datos con conocimientos de Excel. Apoyo en la actualización de registros.", method: "groq-ai" } });
    if (path.endsWith("/writing/generate")) {
      writing.unshift({ id: "draft", status: "prepared", index: 0, before: profile.experiences[0].description, after: "Apoyé la actualización de registros con Excel.", method: "groq-ai", record: profile.experiences[0], questions: [] });
      return route.fulfill({ json: writing[0] });
    }
    if (path.endsWith("/coach")) return route.fulfill({ json: { source_version: "saved-profile-version", experiences: profile.experiences, writing, writing_service: { ...service, available } } });
    if (path.endsWith("/matching/evidence")) return route.fulfill({ json: [] });
    if (path.endsWith("/profiles/me")) {
      if (request.method() === "PUT") profile = { ...profile, ...request.postDataJSON() };
      return route.fulfill({ json: profile });
    }
    return route.abort();
  });
  await page.goto(`/quality/?profile=1&theme=${theme}`);
  await expect(page.getByRole("button", { name: "Editar perfil", exact: true })).toBeVisible();
  return { calls, errors };
}

for (const [width, theme] of [[360, "dark"], [1280, "light"]]) test(`Groq summary requires consent and preview before saving · ${theme} · ${width}`, async ({ page }) => {
  const context = await setup(page, { width, theme });
  await page.getByRole("button", { name: "Editar perfil", exact: true }).click();
  await page.getByRole("button", { name: "Preparar resumen", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Un nuevo resumen para tu perfil", exact: true });
  const generate = dialog.getByRole("button", { name: "Generar propuesta", exact: true });
  await expect(generate).toBeDisabled();
  await expect(dialog.getByText(/se enviarán a Groq/)).toBeVisible();
  expect(context.calls).toEqual([]);
  await dialog.getByRole("checkbox", { name: /Autorizo enviar/ }).check();
  await generate.click();
  await expect(dialog.getByRole("textbox", { name: "Propuesta de resumen profesional" })).toHaveValue(/Soy analista de datos/);
  expect(context.calls).toEqual([{ path: "/api/v1/profiles/me/summary/generate", body: expect.objectContaining({ external_ai_consent: true }) }]);
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expect.poll(() => dialog.evaluate((node) => node.scrollWidth <= node.clientWidth + 1)).toBe(true);
  await dialog.screenshot({ path: `../.local/groq-writing-20261103/summary-${theme}-${width}.png` });
  await dialog.getByRole("button", { name: "Usar este texto", exact: true }).click();
  await expect(page.getByRole("textbox", { name: /Tu resumen profesional/ })).toHaveValue(/Soy analista de datos/);
  expect(context.calls).toHaveLength(1);
  await page.getByRole("button", { name: "Guardar cambios", exact: true }).click();
  await expect(page.getByText("Hoja de vida actualizada correctamente", { exact: true })).toBeVisible();
  expect(context.calls.filter((row) => row.path.endsWith("/profiles/me"))).toHaveLength(1);
  expect(context.errors).toEqual([]);
});

test("Groq experience sends only after consent and resets authorization for another experience", async ({ page }) => {
  const context = await setup(page);
  await page.getByRole("button", { name: /Ideas para mejorar tu hoja de vida/ }).click();
  await page.getByRole("tab", { name: "Mejorar un texto", exact: true }).click();
  const generate = page.getByRole("button", { name: "Generar una propuesta con IA", exact: true });
  await expect(generate).toBeDisabled();
  const consent = page.getByRole("checkbox", { name: /Autorizo enviar/ });
  await consent.check();
  await generate.click();
  await expect(page.getByRole("heading", { name: "Tu propuesta está lista", exact: true })).toBeVisible();
  expect(context.calls).toEqual([{ path: "/api/v1/profiles/me/coach/writing/generate", body: expect.objectContaining({ experience_index: 0, external_ai_consent: true }) }]);
  await page.locator("#coach-experience").selectOption("1");
  await expect(consent).not.toBeChecked();
  await expect(generate).toBeDisabled();
  expect(context.errors).toEqual([]);
});

test("Unconfigured Groq cannot submit a summary", async ({ page }) => {
  const context = await setup(page, { available: false });
  await page.getByRole("button", { name: "Editar perfil", exact: true }).click();
  await page.getByRole("button", { name: "Preparar resumen", exact: true }).click();
  await page.getByRole("checkbox", { name: /Autorizo enviar/ }).check();
  await expect(page.getByRole("button", { name: "Generar propuesta", exact: true })).toBeDisabled();
  expect(context.calls).toEqual([]);
});
