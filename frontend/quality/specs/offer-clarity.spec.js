import { test, expect } from "@playwright/test";

const scale = [["A", "Excelente", 90, 100], ["B", "Buena", 75, 89], ["C", "Por mejorar", 50, 74], ["D", "Inicial", 0, 49]].map(([code, label, minimum, maximum]) => ({ code, label, minimum, maximum, description: "Información de funciones, requisitos y condiciones." }));
const job = { id: 71, company_id: 12, company_name: "Empresa de revisión", title: "Analista de datos", location: "Medellín", modality: "hybrid", source_kind: "internal", skills: ["excel"], status: "active", created_at: "2026-10-24T12:00:00Z", description: "Organiza datos para apoyar decisiones del equipo.", requirements: "Manejo de hojas de cálculo", quality_summary: { score: 82, level: "A", rating: scale[1], rating_scale: scale }, quality_details: {}, languages: [], application_questions: [] };
const external = { ...job, id: 72, title: "Analista externo", source_kind: "external", source_url: "https://example.com/job", external_portal: "Portal externo" };
const matches = [job, external].map((row) => ({ id: row.id, job_id: row.id, match_percentage: 75, reasons: ["Buena alineación"], matched_skills: ["excel"], missing_skills: [], quality_score: 82, data_confidence_percentage: 100 }));

for (const width of [360, 1280]) for (const theme of ["light", "dark"]) test(`Clarity levels agree across recommendations, vacancies and detail · ${width} · ${theme}`, async ({ page }) => {
  const errors = []; page.on("pageerror", (error) => errors.push(error.message));
  await page.setViewportSize({ width, height: 950 });
  await page.addInitScript((value) => localStorage.setItem("talentsync_theme", value), theme);
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url()), path = url.pathname.replace("/api/v1", "");
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    if (path === "/notifications/unread-count") return route.fulfill({ json: { count: 0 } });
    if (path === "/jobs") return route.fulfill({ json: [job, external] });
    if (path === "/jobs/71") return route.fulfill({ json: job });
    if (path === "/jobs/71/match") return route.fulfill({ json: matches[0] });
    if (path === "/recommendations/me/jobs/batch") return route.fulfill({ json: { items: matches, pending: 0 } });
    if (path === "/account/privacy") return route.fulfill({ json: { personalize_recommendations: false } });
    if (path === "/profiles/me") return route.fulfill({ json: { skills: ["excel"], experiences: [], preferences: {} } });
    if (path === "/matching/preferences") return route.fulfill({ json: {} });
    if (path.startsWith("/learning/jobs/")) return route.fulfill({ json: { gaps: [{ skill: "excel" }], resources: [{ id: "course-review", title: "Curso de hojas de cálculo", provider: "Proveedor de revisión", skills: ["excel"], targeted_skills: ["excel"], hours: 2, cost: "free", url: "https://example.com/course" }] } });
    if (["/applications/me", "/personalization/feedback", "/matching/evidence", "/learning/plans"].includes(path)) return route.fulfill({ json: [] });
    return route.fulfill({ status: 404, json: { detail: "Ruta no prevista en esta revisión" } });
  });
  for (const path of ["/recomendaciones", "/vacantes", "/vacantes/71"]) {
    await page.goto(`/quality/?entry=1&signed=candidate&theme=${theme}&path=${encodeURIComponent(path)}`);
    await expect(page.getByLabel("Nivel B de claridad: Buena", { exact: true })).toHaveCount(1);
    await expect(page.getByText(/Claridad de oferta \d+%/)).toHaveCount(0);
    if (path === "/recomendaciones") {
      const recommendation = page.locator(".recommendation-card").first();
      await expect(recommendation.getByRole("button", { name: "Postularme", exact: true })).toHaveCSS("cursor", "pointer");
      await expect(recommendation.getByRole("link", { name: "Ver detalle", exact: true })).toHaveCSS("cursor", "pointer");
      await recommendation.getByRole("button", { name: "Ver compatibilidad y formación", exact: true }).click();
      const disclosure = recommendation.locator(".vacancy-learning-disclosure");
      const counter = disclosure.locator(".vacancy-resource-count");
      await expect(counter).toHaveText("1 recurso");
      await expect(counter).toHaveCSS("cursor", "pointer");
      await expect(disclosure.locator("summary svg").last()).toHaveCSS("cursor", "pointer");
      await counter.click();
      await expect(disclosure).toHaveAttribute("open", "");
      await expect(disclosure.getByRole("heading", { name: "Curso de hojas de cálculo", exact: true })).toBeVisible();
      await disclosure.locator(".vacancy-learning-chevron").click();
      await expect(disclosure).not.toHaveAttribute("open", "");
    }
    if (path === "/vacantes/71") {
      await expect(page.locator(".offer-clarity-guide")).toHaveCount(0);
      const current = page.locator(".offer-clarity-current");
      await expect(current.locator(".offer-clarity-letter")).toHaveText("B");
      await expect(current).toContainText("Información clara del cargo, con algunos detalles por completar.");
      await expect(current).not.toContainText("Excelente");
      await current.screenshot({ path: `../.local/pointer-clarity-review/current-${theme}-${width}.png` });
    }
    await expect(page.locator(".offer-clarity-guide")).toHaveCount(0);
    if (path === "/vacantes") {
      await expect(page.locator(".vacancy-card").filter({ hasText: "Analista externo" }).locator(".offer-clarity-badge")).toHaveCount(0);
      await page.screenshot({ path: `../.local/course-completion-review/clarity-${theme}-${width}.png`, fullPage: true });
    }
    await page.evaluate(async () => {
      document.documentElement.style.fontSize = "200%";
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });
    const geometry = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth, elements: [...document.querySelectorAll("body *")].filter((node) => node.getBoundingClientRect().right > innerWidth + 1).slice(0, 12).map((node) => ({ tag: node.tagName, class: String(node.className), width: Math.round(node.getBoundingClientRect().width) })) }));
    expect(geometry.overflow, JSON.stringify({ path, ...geometry })).toBeLessThanOrEqual(1);
  }
  expect(errors).toEqual([]);
});
