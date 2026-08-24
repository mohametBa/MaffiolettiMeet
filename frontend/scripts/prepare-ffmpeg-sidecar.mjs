/**
 * Prépare le sidecar ffmpeg attendu par tauri.conf.json (`externalBin`).
 *
 * L'amont déclare `binaries/ffmpeg` mais ne fournit rien pour le provisionner :
 * sans ce fichier, le bundle échoue — et à l'exécution l'app irait télécharger
 * ffmpeg toute seule depuis Internet (voir src-tauri/src/audio/ffmpeg.rs), ce
 * qu'on ne veut pas pour une app qui doit rester locale.
 *
 * On copie donc le binaire statique du paquet npm `ffmpeg-static` sous le nom
 * attendu par Tauri : ffmpeg-<target-triple>[.exe].
 *
 * Usage : node scripts/prepare-ffmpeg-sidecar.mjs
 */
import { execFileSync } from 'node:child_process';
import { copyFileSync, chmodSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const here = dirname(fileURLToPath(import.meta.url));
const binariesDir = join(here, '..', 'src-tauri', 'binaries');

const source = require('ffmpeg-static');
if (!source || !existsSync(source)) {
  console.error("ffmpeg-static n'est pas installé. Lancez `pnpm install` d'abord.");
  process.exit(1);
}

const verbose = execFileSync('rustc', ['-vV'], { encoding: 'utf8' });
const triple = verbose.match(/^host:\s*(\S+)$/m)?.[1];
if (!triple) {
  console.error("Impossible de déterminer le target triple (rustc -vV).");
  process.exit(1);
}

mkdirSync(binariesDir, { recursive: true });
const dest = join(binariesDir, `ffmpeg-${triple}${triple.includes('windows') ? '.exe' : ''}`);
copyFileSync(source, dest);
chmodSync(dest, 0o755);
console.log(`sidecar ffmpeg : ${dest}`);
