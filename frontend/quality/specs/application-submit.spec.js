import { test, expect } from "@playwright/test";

for (const width of [360, 1440]) for (const theme of ["light", "dark"]) test(`CV attachment · ${width}px · ${theme}`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 950 });
  const errors = [], payloads = [];
  const versionId = "a".repeat(32);
  const job = { id: 101, title: "Analista de inventarios y coordinación de entregas", company_name: "Distribución de ejemplo", application_questions: [{ id: "example-question", prompt: "¿Cómo verificaste las diferencias de inventario?", required: true, type: "open" }] };
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    if (url.pathname.endsWith("/jobs/101/preparation")) return route.fulfill({ json: { profile: { resume_options: { sections: ["summary", "experiences"], include_photo: false } }, versions: [{ id: versionId, label: "Frontend · React", filename: "Hoja de vida.pdf", created_at: "2026-10-22T12:00:00Z" }] } });
    if (url.pathname.endsWith("/jobs/101")) return route.fulfill({ json: job });
    if (url.pathname.endsWith("/applications") && route.request().method() === "POST") { const body = route.request().postDataJSON(); payloads.push(body); return route.fulfill({ status: 201, json: { id: 901, job_id: 101, status: "submitted" } }); }
    throw new Error(`Unexpected request: ${url.pathname}`);
  });
  await page.goto(`/quality/?submit=1&theme=${theme}`);
  const dialog = page.getByRole("dialog", { name: "Revisa tu postulación", exact: true });
  await expect(dialog.getByText(job.application_questions[0].prompt, { exact: false })).toBeVisible();
  expect(payloads).toHaveLength(0);
  await dialog.getByRole("button", { name: "Elegir CV", exact: true }).click();
  await expect(dialog.getByRole("alert")).toContainText("Responde la pregunta");
  await dialog.getByRole("textbox").fill("Comparé los movimientos y documenté las diferencias encontradas.");
  await dialog.getByRole("button", { name: "Elegir CV", exact: true }).click();
  await expect(dialog.getByRole("radio", { name: /Mi CV del perfil/ })).toBeChecked();
  await expect(dialog.getByText("2 apartados · Sin foto", { exact: true })).toBeVisible();
  await expect(dialog.getByRole("link", { name: /Cambiar preferencias en mi perfil/ })).toHaveAttribute("href", "/perfil");
  await testInfo.attach("confirmación-cv", { body: await page.screenshot({ animations: "disabled" }), contentType: "image/png" });
  await dialog.getByRole("button", { name: "Enviar postulación", exact: true }).click();
  await expect(page.getByText("Postulación enviada", { exact: true })).toBeVisible();
  expect(payloads[0]).toMatchObject({ job_id: 101, attach_resume: true, resume_version_id: null, screening_answers: [{ question_id: "example-question", answer: "Comparé los movimientos y documenté las diferencias encontradas." }] });
  for (const choice of ["version", "none"]) {
    await page.getByRole("button", { name: "Postularme", exact: true }).click();
    await dialog.getByRole("textbox").fill("Verifiqué los registros originales.");
    await dialog.getByRole("button", { name: "Elegir CV", exact: true }).click();
    await dialog.locator(`input[value="${choice}"]`).check();
    if (choice === "version") await expect(dialog.getByRole("option", { name: /Frontend · React/ })).toHaveCount(1);
    await dialog.getByRole("button", { name: "Enviar postulación", exact: true }).click();
    await expect(dialog).toHaveCount(0);
  }
  expect(payloads).toHaveLength(3);
  expect(payloads[1]).toMatchObject({ attach_resume: true, resume_version_id: versionId });
  expect(payloads[2]).toMatchObject({ attach_resume: false, resume_version_id: null });
  await page.getByRole("button", { name: "Postularme", exact: true }).click();
  await dialog.getByRole("button", { name: "Cancelar", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  expect(payloads).toHaveLength(3);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});
