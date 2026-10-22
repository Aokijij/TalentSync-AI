import { test, expect } from "@playwright/test";

for (const width of [360, 1440]) for (const theme of ["light", "dark"]) test(`National radar · ${width}px · ${theme}`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 950 });
  const errors = [], requests = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) return route.abort();
    if (!url.pathname.startsWith("/api/")) return route.continue();
    if (url.pathname.endsWith("/profiles/me")) return route.fulfill({ json: { location: "Medellín", skills: ["python"], experiences: [], preferences: {}, desired_salary: 0 } });
    if (url.pathname.endsWith("/profiles/me/market")) {
      const query = Object.fromEntries(url.searchParams); requests.push(query);
      const suggestion = { family: "software", level: "junior", location: "Medellín", location_scope: "city" };
      const filters = query.personalized === "true" ? suggestion : { ...query, location: query.location_scope === "country" ? "" : query.location };
      const national = filters.location_scope === "country";
      return route.fulfill({ json: { as_of: "2026-10-22T12:00:00Z", since: "2026-07-24", filters, suggested_filters: suggestion, families: { software: "Tecnología y desarrollo" }, participation: {}, local_data: true,
        demand: { as_of: "2026-10-22T12:00:00Z", since: "2026-07-24", sample: national ? 40 : 20, skills: [], own_skills: [], jobs: [], sources: {}, note: "Ofertas observadas para el ejemplo." },
        peers: { status: "ready", sample: national ? 40 : 20, minimum_sample: 20, skills: [], note: "Habilidades declaradas, sin datos personales." },
        salary: { status: "ready", offers: [], groups: [{ modality: "onsite", contract_type: "indefinite", employment_type: "full_time", weekly_hours: 40, sample: 20, offers: 40, median: 3000000, p25: 2500000, p75: 3500000 }], minimum_sample: 20, note: "Mínimos publicados del ejemplo." } } });
    }
    throw new Error(`Unexpected request: ${url.pathname}`);
  });
  await page.goto(`/quality/?radar=1&theme=${theme}`);
  const scope = page.getByRole("combobox", { name: "Ubicación", exact: true });
  await expect(scope).toHaveValue("city");
  await expect(page.getByRole("combobox", { name: "Ciudad", exact: true })).toHaveValue("Medellín");
  await testInfo.attach("radar-filtros-ciudad", { body: await page.locator(".market-filters").screenshot({ animations: "disabled" }), contentType: "image/png" });
  await scope.selectOption("country");
  await expect(page.getByRole("combobox", { name: "Ciudad", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Actualizar radar", exact: true }).click();
  await expect(page.locator(".market-scope")).toHaveText("Todo el país");
  expect(requests.at(-1)).toMatchObject({ location_scope: "country", family: "software", level: "junior" });
  expect(requests.at(-1).location || "").toBe("");
  await expect(page.getByText("40 ofertas consultadas", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Perfiles comparables", exact: true }).click();
  await expect(page.getByText("40 perfiles participantes", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Salarios", exact: true }).click();
  await expect(page.getByText("Mediana", { exact: true })).toBeVisible();
  await testInfo.attach("radar-nacional", { body: await page.screenshot({ fullPage: true, animations: "disabled" }), contentType: "image/png" });
  await page.getByRole("button", { name: "Usar mi perfil", exact: true }).click();
  await expect(scope).toHaveValue("city");
  await expect(page.getByRole("combobox", { name: "Ciudad", exact: true })).toHaveValue("Medellín");
  await expect(page.locator(".market-scope")).toHaveText("Medellín");
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});
