import test from "node:test";
import assert from "node:assert/strict";
import worker, { backendOrigin, handleRequest } from "../../infra/production/cloudflare-worker.mjs";

const proxyEnvironment = { API_ORIGIN: "https://api.example.com", API_PROXY_SECRET: "a".repeat(64) };

test("production proxy refuses unsafe origins and a loop back to Pages", async () => {
  for (const value of [undefined, "http://api.example.com", "https://user:secret@api.example.com", "https://localhost", "https://api.example.com/path", "https://api.example.com?key=secret", "https://api.example.com:8443"]) {
    assert.equal(backendOrigin(value), null);
  }
  assert.equal(backendOrigin("https://api.example.com"), "https://api.example.com");
  const response = await handleRequest(new Request("https://talentsync-ai.pages.dev/api/v1/auth/me"), { API_ORIGIN: "https://talentsync-ai.pages.dev" }, () => assert.fail("proxy loop"));
  assert.equal(response.status, 503);
});

test("private API request keeps session, CSRF, query and redirect cookies without caching", async () => {
  const request = new Request("https://talentsync-ai.pages.dev/api/v1/auth/social/google/callback?code=synthetic&state=test", {
    headers: { Cookie: "talentsync_oauth_browser=synthetic", "X-CSRF-Token": "csrf", Origin: "https://talentsync-ai.pages.dev", "X-Forwarded-For": "spoofed" },
  });
  const response = await handleRequest(request, proxyEnvironment, async (url, init) => {
    assert.equal(url.href, "https://api.example.com/api/v1/auth/social/google/callback?code=synthetic&state=test");
    assert.equal(init.headers.get("Cookie"), "talentsync_oauth_browser=synthetic");
    assert.equal(init.headers.get("X-CSRF-Token"), "csrf");
    assert.equal(init.headers.get("Origin"), "https://talentsync-ai.pages.dev");
    assert.equal(init.headers.has("X-Forwarded-For"), false);
    assert.equal(init.headers.get("X-TalentSync-Proxy-Secret"), proxyEnvironment.API_PROXY_SECRET);
    assert.equal(init.redirect, "manual");
    const headers = new Headers({ Location: "https://talentsync-ai.pages.dev/candidato" });
    headers.append("Set-Cookie", "talentsync_session=synthetic; Secure; HttpOnly; Path=/");
    headers.append("Set-Cookie", "talentsync_csrf=csrf; Secure; Path=/");
    return new Response(null, { status: 303, headers });
  });
  assert.equal(response.status, 303);
  assert.equal(response.headers.getSetCookie().length, 2);
  assert.equal(response.headers.get("Cache-Control"), "no-store");
});

test("API accepts a streamed upload, static navigation uses Pages and upstream failure stays JSON", async () => {
  const upload = new Request("https://talentsync-ai.pages.dev/api/v1/profiles/me/cv", { method: "POST", body: "synthetic-file" });
  await handleRequest(upload, proxyEnvironment, async (_url, init) => {
    assert.equal(init.method, "POST");
    assert.equal(await new Response(init.body).text(), "synthetic-file");
    return Response.json({ ok: true });
  });
  const staticResult = await handleRequest(new Request("https://talentsync-ai.pages.dev/login"), { ASSETS: { fetch: () => new Response("SPA") } });
  assert.equal(await staticResult.text(), "SPA");
  const failed = await handleRequest(new Request("https://talentsync-ai.pages.dev/health/ready"), proxyEnvironment, () => { throw new Error("private upstream error"); });
  assert.equal(failed.status, 503);
  assert.doesNotMatch(await failed.text(), /private upstream/);
});

test("Cloudflare entrypoint accepts ExecutionContext and overwrites forged proxy metadata", async (t) => {
  t.mock.method(globalThis, "fetch", async (_url, init) => {
    assert.equal(init.headers.get("X-TalentSync-Client-IP"), "198.51.100.5");
    assert.equal(init.headers.get("X-TalentSync-Proxy-Secret"), proxyEnvironment.API_PROXY_SECRET);
    return Response.json({ status: "ready" });
  });
  const request = new Request("https://talentsync-ai.pages.dev/health/ready", { headers: {
    "CF-Connecting-IP": "198.51.100.5", "X-TalentSync-Client-IP": "spoofed", "X-TalentSync-Proxy-Secret": "spoofed",
  } });
  const response = await worker.fetch(request, proxyEnvironment, { waitUntil() {} });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).status, "ready");
});
