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

### macOS (Apple Silicon)

Prérequis : Node 20+, pnpm, Rust stable, cmake, Xcode Command Line Tools.

```bash
cd frontend
pnpm install
./scripts/build-ffmpeg-lgpl.sh            # une fois : compile le ffmpeg redistribuable
node scripts/prepare-ffmpeg-sidecar.mjs   # installe le sidecar
./build-gpu.sh                            # détecte le GPU, compile llama-helper puis l'app
```

Le premier build compile whisper.cpp et llama.cpp : 15–30 min et plusieurs Go.
Le `.dmg` sort dans `target/release/bundle/dmg/`.

Le binaire produit est spécifique à l'architecture : un build Apple Silicon ne
tourne **pas** sur un Mac Intel. Pour un poste Intel, refaire le build sur un
Mac Intel (les scripts sont les mêmes).

### Windows

Le build Windows doit se faire **sur une machine Windows** : whisper.cpp et
llama.cpp sont compilés avec MSVC, il n'y a pas de compilation croisée depuis
macOS.

Prérequis : Node 20+, pnpm, Rust stable (toolchain `x86_64-pc-windows-msvc`),
Visual Studio Build Tools avec la charge de travail « Développement Desktop
en C++ », CMake, Git.

```powershell
cd frontend
pnpm install
powershell -ExecutionPolicy Bypass -File scripts\fetch-ffmpeg-windows.ps1
node scripts/prepare-ffmpeg-sidecar.mjs
.\build-gpu.bat
```

⚠️ **Ne pas utiliser `build.ps1`** : ce script exige `TAURI_SIGNING_PRIVATE_KEY`,
qui servait à signer les artefacts d'updater qu'on ne produit plus. Il refusera
de démarrer. `build-gpu.bat` fait le vrai travail.

Le `.msi` et l'installeur NSIS sortent dans `target\release\bundle\`.

### Le sidecar ffmpeg

`tauri.conf.json` déclare `externalBin: ["binaries/llama-helper", "binaries/ffmpeg"]`.
`build-gpu.sh` fabrique bien `llama-helper`, mais **rien dans l'amont ne fournit
`ffmpeg`** : sans lui le bundle échoue, et à l'exécution l'app irait le
télécharger toute seule sur Internet puis l'installer dans `~/.local/bin`
(`src-tauri/src/audio/ffmpeg.rs`) — exactement ce qu'on ne veut pas.

L'app ne demande à ffmpeg que deux choses : encoder en AAC/MP4 (encodeur natif)
et décoder des fichiers audio. Aucun composant GPL n'est nécessaire, donc on
utilise une build **LGPL v2.1**, seule redistribuable :

- macOS : `scripts/build-ffmpeg-lgpl.sh` compile ffmpeg 7.1.1 depuis les sources
  officielles, en statique, sans dépendance externe (`--disable-autodetect`) et
  sans pile réseau (`--disable-network` : ffmpeg ne peut pas ouvrir d'URL).
- Windows : `scripts/fetch-ffmpeg-windows.ps1` récupère la build **lgpl** de
  BtbN/FFmpeg-Builds.

`scripts/prepare-ffmpeg-sidecar.mjs` copie ensuite le binaire sous le nom attendu
par Tauri et **refuse** un binaire compilé `--enable-gpl` ou `--enable-nonfree`.
`src-tauri/vendor/` et `src-tauri/binaries/` sont dans le `.gitignore` : ces deux
étapes sont à refaire après chaque clone.

Conformité LGPL : conserver `scripts/build-ffmpeg-lgpl.sh`. Il contient la
version exacte et la ligne de configuration, ce qui suffit à reconstruire le
binaire à l'identique depuis les sources publiques — c'est ce que la licence
demande de pouvoir fournir.

## Distribuer l'app en interne

Le DMG fait une quarantaine de Mo, tout est dedans (modèles exclus, voir plus bas).

### macOS — Gatekeeper

L'app est signée en ad-hoc (`signingIdentity: "-"`), pas avec un certificat
Apple. Conséquence : si le fichier arrive avec l'attribut de **quarantaine**
(navigateur, mail, Drive, Slack), macOS refuse de l'ouvrir. Depuis macOS 15,
le raccourci « clic droit → Ouvrir » ne suffit plus : il faut passer par
**Réglages Système → Confidentialité et sécurité → « Ouvrir quand même »**.

Deux contournements :

- **Transporter le DMG par partage réseau interne (SMB) ou AirDrop** : ces
  chemins ne posent pas l'attribut de quarantaine, l'app s'ouvre normalement.
- **Retirer la quarantaine à la main** après installation :
  `xattr -dr com.apple.quarantine "/Applications/Maffioletti Meet.app"`

La vraie solution, au-delà de quelques postes : un compte Apple Developer
(99 $/an), un certificat *Developer ID Application* et la notarisation. Tauri
s'en charge si `APPLE_ID`, `APPLE_PASSWORD` et `APPLE_TEAM_ID` sont dans
l'environnement au moment du build (sinon il affiche `skipping app notarization`).

### Windows — SmartScreen

Sans certificat de signature de code, SmartScreen affiche « Windows a protégé
votre ordinateur » au premier lancement : *Informations complémentaires* →
*Exécuter quand même*. Un certificat OV (~200–400 €/an) fait disparaître
l'avertissement une fois la réputation établie ; un certificat EV le fait
disparaître immédiatement.

### Premier démarrage

L'app demande l'accès au micro et à l'enregistrement d'écran, puis télécharge
les modèles (Whisper pour la transcription, un modèle de langue pour les
résumés) depuis Hugging Face — plusieurs centaines de Mo à plusieurs Go selon le
modèle. Ce téléchargement part du code Rust, qui n'est pas soumis à la CSP.
Aucune donnée de réunion ne sort du poste ; l'app va chercher ses modèles une
fois, à l'installation.

## Reste à faire

- **Build Windows** : à produire sur une machine Windows (voir plus haut).
- **Italianisation de l'interface** (`frontend/src/`), chantier à part.
- **Signature** : compte Apple Developer et/ou certificat de signature Windows,
  si les avertissements au premier lancement posent problème.

## Au rebase, vérifier en priorité

Ces trois points sont ceux que l'amont peut réintroduire silencieusement :

```bash
grep -rn "posthog\|phc_" frontend/src-tauri/src/
grep -n "updater" frontend/src-tauri/tauri.conf.json frontend/src-tauri/src/lib.rs
grep -n "connect-src" frontend/src-tauri/tauri.conf.json
```
