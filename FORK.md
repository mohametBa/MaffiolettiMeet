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

## Reste à faire

- **Icônes** : fournir un PNG carré 1024×1024 du logo Maffioletti puis
  `cd frontend && pnpm tauri icon chemin/vers/logo-1024.png`.
  `bundle.icon` pointe déjà vers `icons/icon.png|icns|ico`, les noms que la
  commande produit.
- **Italianisation de l'interface** (`frontend/src/`), chantier à part.
- **Premier build** : `cd frontend && pnpm install && pnpm tauri build:metal`
  (compte 15–30 min la première fois, whisper.cpp est compilé).

## Au rebase, vérifier en priorité

Ces trois points sont ceux que l'amont peut réintroduire silencieusement :

```bash
grep -rn "posthog\|phc_" frontend/src-tauri/src/
grep -n "updater" frontend/src-tauri/tauri.conf.json frontend/src-tauri/src/lib.rs
grep -n "connect-src" frontend/src-tauri/tauri.conf.json
```
