# Maffioletti Meet — fork de Meetily

Ce dépôt est un fork de [Zackriya-Solutions/meeting-minutes](https://github.com/Zackriya-Solutions/meeting-minutes)
(Meetily, licence MIT). Le fichier `LICENSE.md` et la mention de copyright
Zackriya Solutions sont conservés ; l'écran « À propos » de l'application indique
« Basato su Meetily (licenza MIT) ».

Le plan complet est dans [PLAN_App_Maffioletti_Meet.md](PLAN_App_Maffioletti_Meet.md).

## Remotes

| Remote | URL | Usage |
|---|---|---|
| `origin` | https://github.com/mohametBa/MaffiolettiMeet | notre fork, branche `maffioletti` |
| `upstream` | https://github.com/Zackriya-Solutions/meeting-minutes | amont, **lecture seule** |

Récupérer les correctifs amont :

```bash
git fetch upstream
git rebase upstream/main        # relire attentivement les conflits (voir plus bas)
```

## Ce que le fork change (commit `chore: dé-branding et dé-télémétrie`)

Tout est regroupé dans un seul commit isolé, pour repérer d'un coup d'œil les
conflits lors d'un rebase sur l'amont.

1. **Updater neutralisé** — l'amont pointait vers les releases GitHub de Zackriya :
   l'app se serait mise à jour toute seule avec le build officiel de Meetily.
   - `frontend/src-tauri/tauri.conf.json` : bloc `plugins.updater` supprimé,
     `createUpdaterArtifacts: false`, permission `updater:default` retirée.
   - `frontend/src-tauri/src/lib.rs` : `tauri_plugin_updater` n'est plus enregistré.
   - `frontend/src/services/updateService.ts` : `UPDATES_ENABLED = false`, le
     `check()` n'est jamais appelé (il échouerait, le plugin n'existant plus).
   - `frontend/src/components/About.tsx` : bouton « Check for Updates » retiré.

   Pour remettre un canal de mise à jour interne plus tard : générer une paire de
   clés (`pnpm tauri signer generate`), publier `latest.json` sur notre repo, et
   remettre les quatre points ci-dessus avec **notre** pubkey.

2. **Télémétrie PostHog supprimée** — `frontend/src-tauri/src/analytics/commands.rs` :
   `api_key: String::new()` et `enabled: false`. `AnalyticsClient::new` ne crée
   alors aucun client ; les commandes `track_*` existent toujours et ne font rien.
   La clé en dur a aussi été retirée de `lib_old_complex.rs` (fichier non compilé).

3. **CSP verrouillée sur la machine** — `connect-src` n'autorise plus que
   `localhost` (11434 Ollama, 5167 backend, 8178 whisper). `https://api.ollama.ai`
   a été retiré : aucune connexion sortante possible depuis le webview.

4. **Signature** — macOS reste en ad-hoc (`signingIdentity: "-"`) : au premier
   lancement, clic droit → Ouvrir. Windows : le `signCommand` a été retiré
   (pas de certificat) ; SmartScreen affichera un avertissement.
   ⚠️ `frontend/build.ps1` exige encore `TAURI_SIGNING_PRIVATE_KEY` (il servait à
   signer les artefacts d'updater) : sous Windows, appeler `build-gpu.bat`
   directement.

5. **Rebranding** — `productName` / `identifier` (`it.maffioletti.meet`) /
   titre de fenêtre / `package.json` / `Cargo.toml`, version repartie à `0.1.0`,
   et les libellés visibles de l'interface.
   ⚠️ Le changement d'`identifier` change l'emplacement des données
   (`$APPDATA`) : une installation Meetily existante sur le même poste ne sera
   pas reprise.

6. **Identité visuelle** — icône de l'app et assets d'interface repris du logo
   Maffioletti. Les fichiers de travail sont dans [`brand/`](brand/) ; le master
   de l'icône est `frontend/src-tauri/app-icon.png` (1024×1024).
   Pour la régénérer après modification :

   ```bash
   cd frontend
   pnpm tauri icon src-tauri/app-icon.png
   rm -rf src-tauri/icons/android src-tauri/icons/ios   # desktop only
   ```

## Construire l'app

Prérequis (installés sur le Mac mini) : Node 20+, pnpm, Rust stable, cmake,
Xcode Command Line Tools.

```bash
cd frontend
pnpm install
node scripts/prepare-ffmpeg-sidecar.mjs   # sidecar ffmpeg, voir ci-dessous
./build-gpu.sh                            # detecte le GPU, compile llama-helper puis l'app
```

Le premier build compile whisper.cpp et llama.cpp : 15–30 min et plusieurs Go.
Le `.dmg` sort dans `target/release/bundle/dmg/`.

### Le sidecar ffmpeg

`tauri.conf.json` déclare `externalBin: ["binaries/llama-helper", "binaries/ffmpeg"]`.
`build-gpu.sh` fabrique bien `llama-helper`, mais **rien dans l'amont ne fournit
`ffmpeg`** : sans lui le bundle échoue, et à l'exécution l'app irait le
télécharger toute seule sur Internet puis l'installer dans `~/.local/bin`
(`src-tauri/src/audio/ffmpeg.rs`) — exactement ce qu'on ne veut pas.

`scripts/prepare-ffmpeg-sidecar.mjs` copie le binaire statique du paquet npm
`ffmpeg-static` sous le nom attendu (`ffmpeg-<target-triple>`). Le dossier
`src-tauri/binaries/` est dans le `.gitignore` : le script est à relancer après
chaque clone.

⚠️ **Licence** : le binaire d'`ffmpeg-static` est compilé en `--enable-gpl
--enable-nonfree`, une combinaison qui n'est pas redistribuable. L'app ne s'en
sert que pour encoder en AAC/MP4 et décoder des fichiers audio — ce que fait
n'importe quelle compilation LGPL de base. **Avant de diffuser le `.dmg`**,
remplacer ce binaire par un build LGPL (ou GPL simple) d'ffmpeg. Le fork
lui-même reste MIT : ffmpeg est appelé comme processus séparé, jamais lié.

## Reste à faire

- **Italianisation de l'interface** (`frontend/src/`), chantier à part.
- **Remplacer le binaire ffmpeg** par un build redistribuable (voir ci-dessus).

## Au rebase, vérifier en priorité

Ces trois points sont ceux que l'amont peut réintroduire silencieusement :

```bash
grep -rn "posthog\|phc_" frontend/src-tauri/src/
grep -n "updater" frontend/src-tauri/tauri.conf.json frontend/src-tauri/src/lib.rs
grep -n "connect-src" frontend/src-tauri/tauri.conf.json
```
