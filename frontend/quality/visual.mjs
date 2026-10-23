import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
const update = process.argv.includes("--update");
// Dedicated, pinned browser: personal Chromium preferences never affect baselines.
const args = [fileURLToPath(new URL("../node_modules/@playwright/test/cli.js", import.meta.url)), "test", "visual-regression.spec.js", ...(update ? ["--update-snapshots"] : [])];
const result = spawnSync(process.execPath, args, { stdio: "inherit", env: { ...process.env, TALENTSYNC_VISUAL_BASELINES: "1" } });
process.exit(result.status ?? 1);
