import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) test(`Vacancy courses match accents, casing and canonical aliases · ${theme}`, async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 950 });
  const resources = Array.from({ length: 6 }, (_, index) => ({ id: `communication-${index}`, title: `Comunicación profesional ${index + 1}`, provider: "Formación de ejemplo", skills: ["COMUNICACIÓN"], targeted_skills: ["comunicacion"], hours: 2, cost: "free", category: "business", kind: "course", instructions: "Practica la comunicación en situaciones de trabajo.", details: { languages: ["Español"] } }));
  resources.push({ ...resources[0], id: "service", title: "Servicio al cliente", skills: ["servicio al cliente"], targeted_skills: [] });
  const writes = [];
  await page.route("**/*", (route) => {
    const request = route.request(), url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    if (request.method() !== "GET") writes.push(request.method());
    if (url.pathname.endsWith("/learning/plans")) return route.fulfill({ json: [] });
    if (url.pathname.endsWith("/learning/jobs/1")) return route.fulfill({ json: { resources, gaps: [{ skill: "comunicación", key: "comunicacion" }, { skill: "Atención al cliente", key: "servicio al cliente" }, { skill: "Excel", key: "excel" }] } });
    return route.abort();
  });
  await page.goto(`/quality/?vacancyLearning=1&theme=${theme}`);
  await page.locator("summary.vacancy-learning-heading").click();
  await page.getByRole("button", { name: "comunicación", exact: true }).click();
  await expect(page.locator(".course-recommendation-toolbar")).toContainText("6 recursos");
  await expect(page.locator(".vacancy-learning-resources article")).toHaveCount(4);
  await page.getByRole("button", { name: /Siguiente/ }).click();
  await expect(page.locator(".vacancy-learning-resources article")).toHaveCount(2);
  await page.getByRole("button", { name: "Atención al cliente", exact: true }).click();
  await expect(page.locator(".course-recommendation-toolbar")).toContainText("1 recurso");
  await expect(page.getByRole("heading", { name: "Servicio al cliente", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Excel", exact: true }).click();
  await expect(page.getByText(/Aún no hay recursos revisados para esta habilidad/)).toBeVisible();
  await page.getByRole("button", { name: "Ver todas las habilidades", exact: true }).click();
  await expect(page.locator(".course-recommendation-toolbar")).toContainText("7 recursos");
  expect(writes).toEqual([]);
});
