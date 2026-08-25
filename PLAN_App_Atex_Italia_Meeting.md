# Atex Italia Meeting — fork du client Meetily

Base : `Zackriya-Solutions/meetily`, dossier `frontend/` (Tauri 2 + Rust + Next.js 15).
Licence MIT : le fork, le rebranding et la distribution interne sont autorisés.
Deux obligations : **conserver le fichier `LICENSE.md` et la mention de copyright
Zackriya Solutions**, et ne pas laisser croire que Atex Italia est l'éditeur
d'origine (un « Basato su Meetily (MIT) » dans l'écran À propos suffit).

---

## 0. Créer le fork en gardant le lien avec l'amont

```bash
git clone https://github.com/Zackriya-Solutions/meetily atex-italia-meeting
cd atex-italia-meeting
git remote rename origin upstream          # l'amont, en lecture seule
git remote add origin <votre-repo-git>     # GitLab Atex Italia
git checkout -b maffioletti
git push -u origin maffioletti
```

Garder `upstream` permet de récupérer les correctifs plus tard avec
`git fetch upstream && git rebase upstream/main`. Sans ça, le fork devient un
cul-de-sac dès la première mise à jour.

---

## 1. Les quatre pièges à désamorcer AVANT de compiler

### 1.1 L'updater pointe vers les releases de Zackriya ⚠️ critique

`frontend/src-tauri/tauri.conf.json` :

```json
"plugins": {
  "updater": {
    "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6…",
    "endpoints": [
      "https://github.com/Zackriya-Solutions/meeting-minutes/releases/latest/download/latest.json"
    ]
  }
}
```

Laissé tel quel, **votre app se mettrait à jour toute seule avec le build officiel
de Meetily**, écrasant votre fork sur les postes. C'est le premier truc à changer.

Le plus simple pour une v1 :

```json
"plugins": {}
```

et dans `"bundle"` : `"createUpdaterArtifacts": false`.
Retirer aussi `"updater:default"` de la liste des `permissions` de la capability
`main`, sinon le build échoue sur une permission d'un plugin absent.

Plus tard, si vous voulez un vrai canal de mise à jour interne : générer votre
propre paire de clés (`pnpm tauri signer generate`), publier `latest.json` sur
votre repo ou derrière le tunnel Cloudflare, et remettre le bloc avec **votre**
pubkey.

### 1.2 La télémétrie PostHog est en dur

`frontend/src-tauri/src/analytics/commands.rs`, ligne 12 :

```rust
api_key: "phc_Aa9PqeCkDkVbtbRsYjtmHANBfcscjCVupxZwrtL5vZ77".to_string(),
```

avec `host: "https://us.i.posthog.com"`. Vos usages partiraient chez l'éditeur,
sur des serveurs US. Le code ne crée le client que si la clé est non vide
(`analytics.rs` : `if config.enabled && !config.api_key.is_empty()`), donc il
suffit de vider la clé :

```rust
api_key: String::new(),
```

Toutes les commandes `track_*` continuent d'exister et ne font plus rien — aucune
autre modification nécessaire. Vérifier ensuite qu'il ne reste aucun appel réseau
sortant : `grep -rn "posthog\|us.i.posthog" src-tauri/src/`.

### 1.3 Restreindre la CSP

Toujours dans `tauri.conf.json` :

```json
"connect-src": "'self' http://localhost:11434 http://localhost:5167 http://localhost:8178 https://api.ollama.ai"
```

L'app étant **indépendante du CRM** (décision actée), aucun domaine externe n'a
besoin d'être ajouté. Au contraire : retirer `https://api.ollama.ai` si vous
n'utilisez qu'Ollama en local. On obtient alors une app dont la CSP n'autorise
que des connexions à la machine elle-même — c'est-à-dire une garantie technique,
vérifiable, que rien ne sort du poste. C'est un argument fort à présenter à la
direction.

### 1.4 La signature

- **macOS** : `"signingIdentity": "-"` = signature ad-hoc. L'app s'ouvre, mais
  Gatekeeper affiche un avertissement au premier lancement (clic droit → Ouvrir).
  Acceptable en interne. Pour l'éviter : compte Apple Developer (99 $/an) et
  notarisation — même coût récurrent que discuté pour l'app mobile.
- **Windows** : `"signCommand"` appelle `scripts/sign-windows.ps1`. Sans
  certificat de signature de code, **retirer cette ligne**, sinon le build casse.
  SmartScreen affichera un avertissement au premier lancement.

---

## 2. Rebranding

| Fichier | Champ | Nouvelle valeur |
|---|---|---|
| `src-tauri/tauri.conf.json` | `productName` | `Atex Italia Meeting` |
| | `identifier` | `it.atexitalia.meeting` |
| | `version` | `0.1.0` (repartir de zéro) |
| | `app.windows[0].title` | `Atex Italia Meeting` |
| `package.json` | `name` | `atex-italia-meeting` |
| `src-tauri/Cargo.toml` | `name`, `description` | idem |

⚠️ Changer l'`identifier` change l'emplacement des données applicatives
(`$APPDATA`). C'est voulu — l'app ne réutilise pas la base SQLite d'une
installation Meetily existante — mais si quelqu'un a déjà testé Meetily sur son
poste, ses enregistrements ne suivront pas.

**Icônes** : préparer un PNG carré 1024×1024 du logo Atex Italia, puis

```bash
cd frontend
pnpm tauri icon chemin/vers/logo-1024.png
```

Tauri régénère tout `src-tauri/icons/` (icns, ico, PNG Windows Store). Vérifier
ensuite que `bundle.icon` liste bien les fichiers générés — le repo pointe vers
`icons/app_icon.icns` et `icons/app_icon.ico`, que la commande ne produit pas
sous ces noms : soit renommer, soit corriger les chemins vers `icons/icon.icns`
et `icons/icon.ico`.

Textes de l'interface : `frontend/src/` (Next.js). L'app est en anglais ;
l'italianisation est un chantier à part, à ne pas mélanger avec le rebranding.

---

## 3. Compiler

Prérequis : Node 20+, pnpm, Rust stable, et les outils de build de la plateforme
(Xcode CLT sur macOS ; Visual Studio Build Tools sur Windows).

```bash
cd frontend
pnpm install
pnpm tauri build                 # CPU
pnpm tauri build:metal           # macOS Apple Silicon (recommandé sur le Mac mini)
```

Attention aux `externalBin` déclarés dans le bundle : `binaries/llama-helper` et
`binaries/ffmpeg` doivent exister avec le suffixe de triple cible
(`ffmpeg-aarch64-apple-darwin`, etc.). Les scripts `build-gpu.sh` / `build.ps1`
du repo s'en occupent — les lire avant de bricoler à la main.

Le premier build compile whisper.cpp : comptez 15–30 minutes et plusieurs Go.

---

## 4. Périmètre : aucune intégration CRM

**Décision actée : l'app est indépendante du CRM.** Pas de bouton d'envoi, pas de
jeton d'API, pas de route d'ingestion. Les enregistrements, transcripts et
résumés restent dans le SQLite local du poste.

Ce que ça implique, pour que ce soit dit une fois :

- Chaque verbale vit sur **un seul poste**. Pas de recherche transverse, pas de
  rattachement à un cliente ou à un affare, rien de partagé avec l'équipe.
- L'export se fait à la main depuis l'app (copier/coller ou fichier), comme avec
  n'importe quel outil de prise de notes local.
- Le module Riunioni du CRM, s'il se fait un jour, reste un **projet distinct**
  avec sa propre source d'alimentation (chemin Teams / upload). Cette app ne le
  nourrit pas.

En contrepartie, le périmètre du fork se réduit à quatre choses — et c'est bien
ce qui le justifie encore :

1. retirer la télémétrie (§ 1.2) ;
2. reprendre le contrôle de l'updater (§ 1.1) ;
3. le rebranding Atex Italia (§ 2) ;
4. à terme, l'italianisation de l'interface.

Si aucune des quatre ne compte vraiment, **installer Meetily tel quel et
désactiver l'analytics dans les réglages** est la solution la moins chère : zéro
développement, zéro fork à maintenir. Le fork ne se justifie que si vous tenez à
la marque, ou si vous voulez la garantie technique du § 1.3.

---

## 5. Distribution interne

- **macOS** : le `.dmg` produit par `pnpm tauri build`, déposé sur un partage
  interne. Premier lancement : clic droit → Ouvrir.
- **Windows** : le `.msi` ou le `.exe` NSIS, même principe.
- Pas d'App Store, pas de store d'entreprise : ce sont des postes gérés en
  interne, la distribution par fichier est légitime et gratuite.

---

## 6. Ce que ce fork ne résout pas

- **Rien pour le mobile.** Tauri 2 sait cibler iOS/Android, mais le cœur audio de
  Meetily est écrit pour desktop (`cpal`, ScreenCaptureKit). Les visites clients
  restent sur la PWA ou le Dictaphone.
- **Rien pour le CRM.** Aucune mémoire d'entreprise, aucune recherche partagée,
  aucun lien avec les affari — c'est le choix assumé du § 4.
- **La maintenance du fork.** Chaque `git rebase upstream/main` peut réintroduire
  la télémétrie ou l'endpoint d'updater : les remettre dans un commit isolé et
  clairement nommé (`chore: dé-branding et dé-télémétrie`) pour repérer les
  conflits d'un coup d'œil.
