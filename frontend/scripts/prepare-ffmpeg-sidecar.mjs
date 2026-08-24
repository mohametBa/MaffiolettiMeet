/**
 * Installe le sidecar ffmpeg attendu par tauri.conf.json (`externalBin`).
 *
 * L'amont déclare `binaries/ffmpeg` mais ne fournit rien pour le provisionner :
 * sans ce fichier, le bundle échoue — et à l'exécution l'app irait télécharger
 * ffmpeg toute seule depuis Internet (voir src-tauri/src/audio/ffmpeg.rs), ce
 * qu'on ne veut pas pour une app qui doit rester locale.
 *
 * Le binaire doit être une build **redistribuable** (LGPL). Il n'est pas dans
 * le dépôt : on le fabrique une fois par plateforme.
 *
 *   macOS   : ./scripts/build-ffmpeg-lgpl.sh
 *   Windows : powershell -ExecutionPolicy Bypass -File scripts\\fetch-ffmpeg-windows.ps1
 *
 * Ce script ne fait que copier le résultat sous le nom attendu par Tauri
 * (`ffmpeg-<target-triple>`), en vérifiant au passage qu'on ne s'apprête pas à
 * embarquer une build GPL ou nonfree.
 *
 * Usage : node scripts/prepare-ffmpeg-sidecar.mjs
 */
import { execFileSync } from 'node:child_process';
import { copyFileSync, chmodSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const vendorDir = join(here, '..', 'src-tauri', 'vendor', 'ffmpeg');
const binariesDir = join(here, '..', 'src-tauri', 'binaries');

function fail(message) {
  console.error(message);
  process.exit(1);
}

let triple;
try {
  const verbose = execFileSync('rustc', ['-vV'], { encoding: 'utf8' });
  triple = verbose.match(/^host:\s*(\S+)$/m)?.[1];
} catch {
  fail("rustc est introuvable : installez Rust, ou ouvrez un nouveau terminal.");
}
if (!triple) fail("Impossible de déterminer le target triple (rustc -vV).");

const exe = triple.includes('windows') ? '.exe' : '';
const source = join(vendorDir, `ffmpeg-${triple}${exe}`);

if (!existsSync(source)) {
  fail(
    `Binaire ffmpeg absent : ${source}\n\n` +
    `Fabriquez-le d'abord :\n` +
    (triple.includes('windows')
      ? `  powershell -ExecutionPolicy Bypass -File scripts\\fetch-ffmpeg-windows.ps1`
      : `  ./scripts/build-ffmpeg-lgpl.sh`)
  );
}

// Garde-fou : une build GPL ou nonfree n'est pas redistribuable.
const banner = execFileSync(source, ['-version'], { encoding: 'utf8' });
const forbidden = ['--enable-gpl', '--enable-nonfree'].filter((f) => banner.includes(f));
if (forbidden.length) {
  fail(
    `Ce ffmpeg est compilé avec ${forbidden.join(' et ')} : il n'est pas redistribuable.\n` +
    `Refabriquez-le avec le script de la plateforme (voir en-tête de ce fichier).`
  );
}

mkdirSync(binariesDir, { recursive: true });
const dest = join(binariesDir, `ffmpeg-${triple}${exe}`);
copyFileSync(source, dest);
chmodSync(dest, 0o755);
console.log(`sidecar ffmpeg : ${dest}`);
console.log(banner.split('\n')[0]);
