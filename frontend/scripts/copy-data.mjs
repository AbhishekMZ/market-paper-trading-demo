// Copies the canonical data files (committed at the repo root in ../public/data)
// into frontend/public/data so Vite can serve them in dev and bundle them on build.
// Vite's publicDir is frontend/public, so we never serve files from outside the root.
// Resilient by design: if the source is missing, log and create an empty target dir
// so the app still builds (the useData hook then renders a friendly placeholder).
import { cp, mkdir, stat, readdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// scripts/ -> frontend/ -> repo root -> public/data
const SRC = resolve(__dirname, '../../public/data');
const DEST = resolve(__dirname, '../public/data');

async function exists(p) {
  try {
    await stat(p);
    return true;
  } catch {
    return false;
  }
}

async function main() {
  await mkdir(DEST, { recursive: true });

  if (!(await exists(SRC))) {
    console.warn(`[copy-data] Source folder not found: ${SRC}`);
    console.warn('[copy-data] Created empty target dir; the app will show placeholders.');
    return;
  }

  await cp(SRC, DEST, { recursive: true });
  const files = await readdir(DEST);
  console.log(`[copy-data] Copied ${files.length} item(s) from ${SRC} -> ${DEST}`);
}

main().catch((err) => {
  // Never fail the build because of data copying — placeholders cover the gap.
  console.warn('[copy-data] Non-fatal error while copying data:', err?.message || err);
});
