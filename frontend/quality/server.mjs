import { build, preview } from "vite";

// Keep each visual run on one compiled revision, without development reloads.
await build({ configFile: "vite.quality.config.js" });
const server = await preview({ configFile: "vite.quality.config.js", preview: { host: "127.0.0.1", port: 4175, strictPort: true } });
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => server.httpServer.close(() => process.exit(0)));
