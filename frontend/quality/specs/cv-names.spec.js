import { test, expect } from "@playwright/test";

for (const width of [360, 1440]) for (const theme of ["light", "dark"]) test(`CV names · ${width}px · ${theme}`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 950 });
  const failures = [], creations = [], renames = [];
  page.on("pageerror", (error) => failures.push(error.message));
  let versions = [];
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    if (url.pathname.endsWith("/preparation")) return route.fulfill({ json: { job: { id: 101, title: "Desarrollador frontend React", company_name: "Empresa de ejemplo" }, source_version: "a".repeat(64), job_version: "b".repeat(64), profile: { summary: "Desarrollo interfaces accesibles.", skills: ["react"], experiences: [], resume_style: "modern", resume_options: { sections: ["summary", "skills"], include_photo: false } }, versions, interview: { questions: [], answers: {}, ask_company: [], version: 0 } } });
    if (url.pathname.endsWith("/cv-versions") && route.request().method() === "POST") {
      const body = route.request().postDataJSON(); creations.push(body);
      const version = { id: "c".repeat(32), label: body.label, created_at: "2026-10-22T12:00:00Z", skills: ["react"], experiences: [], style: "modern", filename: "Hoja de vida.pdf" };
      versions = [version]; return route.fulfill({ status: 201, json: version });
    }
    if (url.pathname.endsWith(`/cv-versions/${"c".repeat(32)}`) && route.request().method() === "PATCH") {
      const body = route.request().postDataJSON(); renames.push(body);
      versions = [{ ...versions[0], label: body.label }]; return route.fulfill({ json: versions[0] });
    }
    throw new Error(`Unexpected request: ${url.pathname}`);
  });
  await page.goto(`/quality/?cvnames=1&theme=${theme}`);
  await page.getByRole("button", { name: /Prepara tu postulación/ }).click();
  const dialog = page.getByRole("dialog", { name: "Prepara tu próxima oportunidad", exact: true });
  await dialog.getByRole("button", { name: "Continuar al diseño", exact: true }).click();
  await dialog.getByRole("textbox", { name: "Nombre del CV", exact: true }).fill("Frontend · React");
  await dialog.getByRole("button", { name: "Guardar versión del CV", exact: true }).click();
  await expect(dialog.locator(".preparation-version-heading strong")).toHaveText("Frontend · React");
  expect(creations[0].label).toBe("Frontend · React");
  await dialog.getByRole("button", { name: /^Renombrar/ }).click();
  await dialog.getByRole("textbox", { name: "Nombre del CV", exact: true }).fill("Frontend · Accesibilidad");
  await dialog.getByRole("button", { name: "Guardar nombre", exact: true }).click();
  await expect(dialog.locator(".preparation-version-heading strong")).toHaveText("Frontend · Accesibilidad");
  await dialog.getByRole("button", { name: "Usar al postularme", exact: true }).click();
  await expect(page.getByText("CV seleccionado: Frontend · Accesibilidad", { exact: true })).toHaveCount(1);
  await dialog.getByRole("button", { name: /^Renombrar/ }).click();
  await dialog.getByRole("textbox", { name: "Nombre del CV", exact: true }).fill("Mi CV de interfaces");
  await dialog.getByRole("button", { name: "Guardar nombre", exact: true }).click();
  await expect(page.getByText("CV seleccionado: Mi CV de interfaces", { exact: true })).toHaveCount(1);
  expect(renames).toEqual([{ label: "Frontend · Accesibilidad" }, { label: "Mi CV de interfaces" }]);
  await dialog.getByRole("button", { name: "Cerrar ventana", exact: true }).click();
  await page.getByRole("button", { name: /Prepara tu postulación/ }).click();
  await dialog.getByRole("button", { name: "Versiones (1)", exact: false }).click();
  await expect(dialog.locator(".preparation-version-heading strong")).toHaveText("Mi CV de interfaces");
  await testInfo.attach("cv-con-nombre", { body: await page.screenshot({ animations: "disabled" }), contentType: "image/png" });
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(failures).toEqual([]);
});
