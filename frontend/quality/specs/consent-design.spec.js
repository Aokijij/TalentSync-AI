import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Consent cards align controls and preserve independent decisions · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1050 });
  await page.addInitScript((theme) => localStorage.setItem("talentsync_theme", theme), theme);
  await page.route("**/*", (route) => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
  await page.goto(`/quality/?auth=complete&theme=${theme}`);
  const identity = page.getByRole("checkbox", { name: /Confirmo que este nombre/ });
  const privacy = page.getByRole("checkbox", { name: /Tratamiento de datos personales/ });
  const terms = page.getByRole("checkbox", { name: /Términos de uso.*He leído/ });
  for (const input of [identity, privacy, terms]) await expect(input).not.toBeChecked();
  const cards = page.locator(".consent-choice");
  for (const card of await cards.all()) {
    const control = card.getByRole("checkbox");
    const inputBox = await control.boundingBox(), copyBox = await card.locator(".consent-choice-copy").boundingBox();
    expect(inputBox.width).toBe(20);
    expect(copyBox.x).toBeGreaterThan(inputBox.x + inputBox.width + 8);
    expect(Math.abs(copyBox.y - inputBox.y)).toBeLessThan(8);
  }
  await privacy.focus(); await page.keyboard.press("Space");
  await expect(privacy).toBeChecked();
  await expect(terms).not.toBeChecked();
  await expect(identity).not.toBeChecked();
  const link = page.getByRole("link", { name: "Leer Política de privacidad" });
  await expect(link).toHaveAttribute("target", "_blank");
  const popup = page.waitForEvent("popup"); await link.click(); await (await popup).close();
  await expect(privacy).toBeChecked();
  await terms.check(); await privacy.uncheck();
  await expect(terms).toBeChecked();
  await expect(privacy).not.toBeChecked();
  await page.locator(".social-registration-card").screenshot({ path: `../.local/consent-design-20261103/registration-${theme}-${width}.png` });
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
});
