// Pages advanced-mode worker: browser sessions and API stay on the same origin.
// API_ORIGIN is a deployment binding containing the backend HTTPS origin.
function unavailable() {
  return Response.json({ detail: "El servicio no está disponible. Inténtalo de nuevo en unos momentos." }, {
    status: 503,
    headers: { "Cache-Control": "no-store", "Retry-After": "30" },
  });
}

export function backendOrigin(value) {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.username || url.password || url.pathname !== "/"
        || url.search || url.hash || url.port && url.port !== "443"
        || !url.hostname.includes(".") || ["localhost", "127.0.0.1"].includes(url.hostname)) return null;
    return url.origin;
  } catch { return null; }
}

export async function handleRequest(request, env, fetchBackend = fetch) {
  const incoming = new URL(request.url);
  if (!(incoming.pathname === "/api" || incoming.pathname.startsWith("/api/")
      || incoming.pathname === "/health" || incoming.pathname.startsWith("/health/"))) {
    return env.ASSETS.fetch(request);
  }
  const origin = backendOrigin(env.API_ORIGIN);
  const proxySecret = env.API_PROXY_SECRET;
  if (!origin || origin === incoming.origin || typeof proxySecret !== "string"
      || !/^[a-f0-9]{64}$/.test(proxySecret)) return unavailable();
  const target = new URL(incoming.pathname + incoming.search, origin);
  const headers = new Headers(request.headers);
  headers.delete("host");
  // Client supplied forwarding headers must never become trusted proxy metadata.
  for (const name of ["forwarded", "x-forwarded-for", "x-forwarded-host", "x-forwarded-proto", "x-real-ip", "x-talentsync-client-ip", "x-talentsync-proxy-secret"]) headers.delete(name);
  headers.set("X-TalentSync-Proxy-Secret", proxySecret);
  headers.set("X-Forwarded-Proto", "https");
  headers.set("X-Forwarded-Host", incoming.hostname);
  const clientIP = request.headers.get("CF-Connecting-IP");
  if (clientIP) {
    headers.set("X-Forwarded-For", clientIP);
    headers.set("X-TalentSync-Client-IP", clientIP);
  }
  try {
    const response = await fetchBackend(target, {
      method: request.method, headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
      redirect: "manual", signal: request.signal,
      // Never cache authentication, private files, or user-specific API results.
      cf: { cacheTtl: 0, cacheEverything: false },
    });
    const result = new Response(response.body, response);
    result.headers.set("Cache-Control", "no-store");
    result.headers.set("X-Content-Type-Options", "nosniff");
    return result;
  } catch { return unavailable(); }
}

// Cloudflare supplies ExecutionContext as the third argument, not a fetch function.
export default { fetch(request, env) { return handleRequest(request, env); } };
