import { test, expect } from "@playwright/test";

const widths = [360, 768, 1280, 1440];
for (const role of ["candidate", "company", "admin"]) for (const theme of ["light", "dark"]) for (const width of widths) {
  test(`${role} · ${theme} · ${width}px`, async ({ page }, testInfo) => {
    const failures = [];
    page.on("pageerror", (error) => failures.push(error.message));
    await page.setViewportSize({ width, height: 950 });
    // The fixture contains no account, token or real API data. Unexpected network
    // access fails instead of consulting a provider during a visual review.
    await page.route("**/*", (route) => {
      const url = new URL(route.request().url());
      return url.hostname === "127.0.0.1" && !url.pathname.startsWith("/api/") ? route.continue() : route.abort();
    });
    await page.goto(`/quality/?role=${role}&theme=${theme}`);
    await expect(page.getByRole("heading", { name: "Prepara tu próxima oportunidad", exact: true })).toBeVisible();
    await expect(page.getByRole("tab", { name: "CV por vacante" })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, "The document must not scroll horizontally").toBeLessThanOrEqual(1);
    for (const card of await page.locator('[data-quality="course"] article.learning-course-card').all()) {
      const cardBox = await card.boundingBox();
      const footer = await card.locator("footer").boundingBox();
      expect(footer.width, "The course footer must span the card").toBeGreaterThanOrEqual(cardBox.width - 3);
      for (const button of await card.locator("footer button").all()) {
        const box = await button.boundingBox();
        expect(box.x).toBeGreaterThanOrEqual(footer.x - 1);
        expect(box.x + box.width).toBeLessThanOrEqual(footer.x + footer.width + 1);
      }
    }
    await page.getByRole("tab", { name: "CV por vacante" }).focus();
    await page.keyboard.press("ArrowRight");
    await expect(page.getByRole("tab", { name: "Practicar entrevista" })).toHaveAttribute("aria-selected", "true");
    const context = page.getByLabel("Contexto", { exact: true });
    await expect(context).toBeVisible();
    await context.fill("Preparábamos una entrega para el equipo.");
    await page.getByLabel("Responsabilidad", { exact: true }).fill("Organizar los registros disponibles.");
    await page.getByLabel("Acción", { exact: true }).fill("Revisé y ordené los registros.");
    await page.getByLabel("Resultado", { exact: true }).fill("El equipo pudo consultar el reporte.");
    await page.getByRole("button", { name: "Guardar mis respuestas" }).click();
    await expect(page.getByText("Respuestas guardadas", { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
    expect(failures).toEqual([]);
    await testInfo.attach("componentes", { body: await page.screenshot({ fullPage: true, animations: "disabled" }), contentType: "image/png" });
  });
}
