// MapLibre 6 loads its background worker from a separate file that it expects
// to sit next to its own code. Next.js bundles MapLibre into its own chunks, so
// that file isn't there. This copies the worker into public/vendor/ (run on
// every npm install), and map-view.tsx points MapLibre at it with setWorkerUrl.
import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const webRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const pkgDir = dirname(require.resolve("maplibre-gl/package.json"));
const outDir = join(webRoot, "public", "vendor");

mkdirSync(outDir, { recursive: true });
copyFileSync(join(pkgDir, "dist", "maplibre-gl-worker.mjs"), join(outDir, "maplibre-gl-worker.mjs"));
console.log("copied maplibre-gl-worker.mjs to public/vendor/");
