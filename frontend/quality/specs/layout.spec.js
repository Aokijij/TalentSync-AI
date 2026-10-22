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
    await page.getByRole("button", { name: "Continuar al diseño" }).click();
    await expect(page.getByRole("button", { name: "Guardar versión del CV", exact: true })).toBeVisible();
    await page.getByRole("button", { name: /Versiones \(0\)/ }).click();
    await expect(page.getByText("Todavía no hay versiones guardadas")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, "The document must not scroll horizontally").toBeLessThanOrEqual(1);
    for (const card of await page.locator('[data-quality="course"] article.learning-course-card').all()) {
      const cardBox = await card.boundingBox();
      const footer = await card.locator("footer").boundingBox();
      const metadata = await card.locator(".course-card-meta").boundingBox();
      const skills = await card.locator(".course-target-skills").boundingBox();
      expect(metadata.x, "Course metadata must keep the card's inner spacing").toBeGreaterThanOrEqual(cardBox.x + 12);
      expect(skills.x, "Reinforced skills must keep the card's inner spacing").toBeGreaterThanOrEqual(cardBox.x + 12);
      expect(footer.width, "The course footer must span the card").toBeGreaterThanOrEqual(cardBox.width - 3);
      for (const button of await card.locator("footer button").all()) {
        const box = await button.boundingBox();
        expect(box.x).toBeGreaterThanOrEqual(footer.x - 1);
        expect(box.x + box.width).toBeLessThanOrEqual(footer.x + footer.width + 1);
      }
    }
    await page.getByRole("button", { name: "Comparar (2)", exact: true }).click();
    const comparison = page.getByRole("dialog", { name: "Compara las vacantes", exact: true });
    await expect(comparison).toBeVisible();
    await expect(comparison.getByRole("columnheader")).toHaveCount(3);
    await expect(comparison.getByRole("cell", { name: "Sin cálculo disponible", exact: true })).toBeVisible();
    await comparison.getByLabel("Mostrar solo condiciones diferentes").check();
    await expect(comparison.getByRole("rowheader", { name: "Idiomas", exact: true })).toHaveCount(0);
    const comparisonRegion = comparison.getByRole("region", { name: "Tabla de comparación de vacantes" });
    const bounds = await comparisonRegion.boundingBox();
    expect(bounds.x).toBeGreaterThanOrEqual(0);
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
    await testInfo.attach("comparador", { body: await page.screenshot({ animations: "disabled" }), contentType: "image/png" });
    await comparison.getByRole("button", { name: "Cerrar ventana" }).click();
    await expect(page.getByRole("button", { name: "Comparar (2)", exact: true })).toBeFocused();
    await expect(page.getByRole("heading", { name: "Tu agenda de entrevistas" })).toBeVisible();
    const tracking = page.locator('[data-quality="tracking"]');
    await expect(tracking.getByRole("tabpanel", { name: "Resumen", exact: true })).toBeVisible();
    await tracking.getByRole("tab", { name: role === "company" ? "Preparar entrevista" : "La vacante", exact: true }).click();
    await expect(tracking.getByText("Revisar los registros de inventario.", { exact: true })).toBeVisible();
    if (role === "company") {
      await tracking.getByRole("tab", { name: "Evaluación interna", exact: true }).click();
      await tracking.getByLabel("Evaluación de ejemplo").fill("Borrador que debe conservarse");
      await tracking.getByRole("tab", { name: "Historial", exact: true }).click();
      await expect(tracking.getByLabel("Evaluación de ejemplo")).toBeHidden();
      await tracking.getByRole("tab", { name: "Evaluación interna", exact: true }).click();
      await expect(tracking.getByLabel("Evaluación de ejemplo")).toHaveValue("Borrador que debe conservarse");
    } else await expect(tracking.getByRole("tab", { name: "Evaluación interna", exact: true })).toHaveCount(0);
    await tracking.getByRole("tab", { name: "Resumen", exact: true }).click();
    await expect(page.getByRole("button", { name: "Añadir al calendario", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Gestionar proceso de ejemplo" }).click();
    const process = page.getByRole("dialog", { name: "Candidata de ejemplo", exact: true });
    await expect(process.getByLabel("Notas internas")).toBeVisible();
    await expect(process.getByText("Respuestas de postulación")).toHaveCount(0);
    const processBox = await process.boundingBox();
    expect(processBox.height).toBeLessThanOrEqual(950 * .85 + 1);
    await process.getByRole("button", { name: "Cerrar", exact: true }).click();
    await page.getByRole("button", { name: "Revisar respuestas de ejemplo" }).click();
    const answerReview = page.getByRole("dialog", { name: "Respuestas de postulación", exact: true });
    await expect(answerReview.getByRole("heading", { name: "¿Cómo verificaste los registros de inventario?" })).toBeVisible();
    await answerReview.getByRole("button", { name: "Siguiente", exact: true }).click();
    await expect(answerReview.getByRole("heading", { name: "¿Cómo compartiste el resultado con el equipo?" })).toBeVisible();
    await answerReview.getByLabel("Valoración manual de la empresa").selectOption("2");
    await answerReview.getByRole("button", { name: "Preparar valoración" }).click();
    await expect(page.getByText("Valoración preparada")).toBeVisible();
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
    await page.getByRole("button", { name: "Empezar práctica", exact: true }).click();
    const practice = page.getByRole("region", { name: "Espacio de práctica", exact: true });
    await expect(practice).toBeVisible();
    await expect(page.getByRole("heading", { name: "Practica una habilidad concreta" })).toHaveCount(0);
    await expect(practice.getByRole("button", { name: "Continuar", exact: true })).toBeDisabled();
    await practice.getByText("def f(items=None) y crear la lista dentro", { exact: true }).click();
    await expect(practice.getByRole("radio", { name: "def f(items=None) y crear la lista dentro", exact: true })).toBeChecked();
    await practice.getByRole("button", { name: "Continuar", exact: true }).click();
    await practice.getByText("Validarlo y comunicar el error", { exact: true }).click();
    await practice.getByRole("button", { name: "Revisar respuestas", exact: true }).click();
    await expect(practice.getByRole("heading", { name: "Revisa tus respuestas", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
    await testInfo.attach("practica", { body: await page.screenshot({ fullPage: true, animations: "disabled" }), contentType: "image/png" });
    await practice.getByRole("button", { name: "Entregar respuestas", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Fundamentos aprobados" })).toBeVisible();
    await page.getByRole("button", { name: "Ver mis resultados", exact: true }).click();
    await expect(page.getByRole("button", { name: "Empezar práctica", exact: true })).toBeVisible();
  });
}
