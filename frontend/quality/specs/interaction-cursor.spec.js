import { test, expect } from "@playwright/test";

for (const role of ["candidate", "company", "admin"]) for (const theme of ["light", "dark"]) test(`Action cursors and hit targets · ${role} · ${theme}`, async ({ page }) => {
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 404, json: {} }));
  await page.goto(`/quality/?design=1&role=${role}&theme=${theme}`);
  for (const selector of [".design-primary", ".design-primary svg", '.ui-workspace-tabs button', '.app-sidebar a[href]', '.app-sidebar a[href] svg']) {
    const action = page.locator(selector).first();
    await expect(action).toBeVisible();
    await expect(action).toHaveCSS("cursor", "pointer");
  }
  const failures = await page.locator("button, a[href], select, [role=button], [role=tab], [role=switch], [role=option], summary").evaluateAll((nodes) => nodes.filter((node) => node.getClientRects().length && !node.matches(":disabled,[aria-disabled=true]")).filter((node) => getComputedStyle(node).cursor !== "pointer").map((node) => ({ tag: node.tagName, text: node.textContent.trim().slice(0, 60), cursor: getComputedStyle(node).cursor })));
  expect(failures).toEqual([]);
  await expect(page.getByRole("button", { name: "Acción no disponible", exact: true })).toHaveCSS("cursor", "not-allowed");
  await expect(page.getByRole("textbox", { name: "Descripción", exact: true })).not.toHaveCSS("cursor", "pointer");
  await page.evaluate(() => {
    const states = document.createElement("section"); states.id = "cursor-states";
    states.innerHTML = '<fieldset disabled><label role="button"><span>Adjuntar archivo</span><input type="file" hidden></label><button><span>Acción deshabilitada</span></button></fieldset><a href="#" aria-disabled="true"><span>Enlace deshabilitado</span></a>';
    document.body.append(states);
  });
  for (const selector of ["#cursor-states label", "#cursor-states label span", "#cursor-states button span", "#cursor-states a span"]) await expect(page.locator(selector)).toHaveCSS("cursor", "not-allowed");
  await page.locator("#cursor-states").evaluate((node) => node.remove());
  const preview = page.getByRole("tab", { name: "Vista previa", exact: true });
  await preview.locator("svg").click();
  await expect(preview).toHaveAttribute("aria-selected", "true");
  await page.getByRole("tab", { name: "Resumen", exact: true }).click();
  const save = page.getByRole("button", { name: "Guardar preferencias", exact: true });
  await save.scrollIntoViewIfNeeded();
  const box = await save.boundingBox();
  await page.mouse.click(box.x + 5, box.y + box.height / 2);
  await expect(page.getByRole("alertdialog", { name: "Guardar preferencias", exact: true })).toBeVisible();
});
