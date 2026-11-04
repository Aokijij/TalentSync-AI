import { test, expect } from "@playwright/test";

for (const theme of ["light", "dark"]) for (const width of [360, 1280]) test(`Real authentication provider completes company entry without reload · ${theme} · ${width}`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  await page.addInitScript(value => localStorage.setItem("talentsync_theme", value), theme);
  let logged = false, pending = true, mfa = false, submitted = false;
  const calls = [], errors = [];
  page.on("pageerror", error => errors.push(error.message));
  const account = () => ({ id: 101, name: "Equipo de ejemplo", email: "owner@example.test", role: "company", email_verified: true, registration_pending: pending, mfa_enabled: mfa });
  const organization = () => ({ id: 41, name: "TalentSync", company_name: "TalentSync", role: "owner", active: true, nit: "INTERNAL-ID", description: "Plataforma de empleo y formación", website: "https://example.test", verification_required: false, verification_kind: "internal", verification_status: submitted ? "reviewing" : "pending", submission: submitted ? { submitted_at: "2026-11-04", kind: "internal" } : {} });
  await page.route("**/api/v1/**", route => {
    const request = route.request(), path = new URL(request.url()).pathname.replace("/api/v1", "");
    calls.push({ path, method: request.method() });
    if (path === "/auth/options") return route.fulfill({ json: { mode: "session", providers: [], company_mfa_required: true, local_mail: false } });
    if (path === "/auth/session/company/login") { logged = true; return route.fulfill({ json: { user: account() } }); }
    if (path === "/auth/me") return route.fulfill({ status: logged ? 200 : 401, json: logged ? account() : { detail: "Inicia sesión" } });
    if (path === "/auth/company/registration/complete") { const p = request.postDataJSON(); expect(p.confirmed && p.data_processing_accepted && p.terms_accepted).toBe(true); pending = false; return route.fulfill({ json: account() }); }
    if (path === "/organization/access") return route.fulfill({ json: organization() });
    if (path === "/organization/me") return route.fulfill({ status: mfa ? 200 : 403, json: mfa ? organization() : { detail: "Configura el autenticador" } });
    if (path === "/account/mfa/setup") return route.fulfill({ json: { secret: "JBSWY3DPEHPK3PXP", uri: "otpauth://totp/Example?secret=JBSWY3DPEHPK3PXP" } });
    if (path === "/account/mfa/confirm") { mfa = true; return route.fulfill({ json: { recovery_codes: ["EXAMPLE-CODE"] } }); }
    if (path === "/organization/internal-review") { expect(request.postDataJSON().accuracy_confirmed).toBe(true); submitted = true; return route.fulfill({ json: organization() }); }
    if (path === "/notifications/unread-count") return route.fulfill({ json: { count: 0 } });
    if (path === "/auth/session/logout") { logged = false; return route.fulfill({ json: {} }); }
    if (["/jobs", "/account/sessions", "/organization/assignments", "/organization/team", "/organization/invitations"].includes(path)) return route.fulfill({ json: [] });
    return route.fulfill({ json: { items: [], total: 0 } });
  });
  await page.goto(`/quality/?entry=1&session=real&path=/empresa/login&theme=${theme}`);
  await page.getByRole("textbox", { name: "Correo de tu cuenta empresarial", exact: true }).fill("owner@example.test");
  await page.getByLabel("Contraseña", { exact: true }).fill("Example-password-2026!");
  await page.getByRole("button", { name: "Entrar a mi empresa", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Prepara tu acceso empresarial", exact: true })).toBeVisible();
  for (const input of await page.getByRole("checkbox").all()) { await expect(input).not.toBeChecked(); await input.check(); }
  await page.getByRole("button", { name: "Confirmar y continuar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Protege tu acceso empresarial", exact: true })).toBeVisible();
  await expect(page.getByText("Propietario", { exact: true })).toBeVisible();
  expect(calls.some(row => row.path === "/organization/me")).toBe(false);
  await page.locator(".company-welcome").screenshot({ path: `../.local/platform-polish-20261104/welcome-${theme}-${width}.png` });
  await page.getByRole("link", { name: "Configurar autenticador", exact: true }).click();
  await page.getByLabel("Contraseña actual", { exact: true }).fill("Example-password-2026!");
  await page.getByRole("button", { name: "Configurar autenticador", exact: true }).click();
  await page.getByRole("textbox", { name: "Código del autenticador", exact: true }).fill("123456");
  await page.getByRole("button", { name: "Activar y obtener recuperación", exact: true }).click();
  await expect(page.getByText("Verificación activa", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Continuar a mi espacio", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Tu espacio está preparado para trabajar", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Revisar espacio interno", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Revisión del espacio interno", exact: true })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "NIT o identificación tributaria", exact: true })).toHaveCount(0);
  await page.getByRole("textbox", { name: "Qué debe revisar administración", exact: true }).fill("Solicito revisar la operación del espacio propio de la plataforma y su responsable.");
  await page.getByRole("checkbox", { name: /Confirmo que administro/ }).check();
  await page.getByRole("button", { name: "Enviar revisión interna", exact: true }).click();
  await expect(page.getByText("Solicitud presentada.", { exact: false }).first()).toBeVisible();
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  const overflow = await page.evaluate(() => ({ amount: document.documentElement.scrollWidth - innerWidth, nodes: [...document.querySelectorAll("body *")].filter(node => node.getBoundingClientRect().right > innerWidth + 1).slice(0, 12).map(node => ({ tag: node.tagName, class: String(node.className), right: node.getBoundingClientRect().right, width: node.getBoundingClientRect().width })) }));
  expect(overflow.amount, JSON.stringify(overflow.nodes)).toBeLessThanOrEqual(1);
  expect(errors).toEqual([]);
});

test("A failed company entry chunk recovers once and exposes a fallback if it remains unavailable", async ({ page }) => {
  let failures = 0, navigations = 0;
  page.on("framenavigated", frame => { if (frame === page.mainFrame()) navigations += 1; });
  await page.route("**/assets/CompanyWelcomePage-*.js", route => { failures += 1; return route.abort("failed"); });
  await page.route("**/api/v1/**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/auth/options")) return route.fulfill({ json: { mode: "session", providers: [], company_mfa_required: true } });
    if (path.endsWith("/auth/me")) return route.fulfill({ json: { id: 101, role: "company", name: "Equipo de ejemplo", email_verified: true, mfa_enabled: false, registration_pending: false } });
    return route.fulfill({ json: { items: [], total: 0 } });
  });
  await page.goto("/quality/?entry=1&session=real&path=/empresa/bienvenida");
  await expect(page.getByRole("heading", { name: "No pudimos abrir esta sección", exact: true })).toBeVisible();
  await expect.poll(() => navigations).toBe(2);
  expect(failures).toBeGreaterThanOrEqual(2);
  await expect(page.getByRole("button", { name: "Recuperar pantalla", exact: true })).toBeVisible();
  await page.unroute("**/assets/CompanyWelcomePage-*.js");
  await page.getByRole("button", { name: "Recuperar pantalla", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Protege tu acceso empresarial", exact: true })).toBeVisible();
});
