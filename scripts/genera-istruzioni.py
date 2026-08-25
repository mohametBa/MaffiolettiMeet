#!/usr/bin/env python3
"""Genere la page ISTRUZIONI.html d'un dossier de distribution.

La page accompagne les installeurs sur le partage interne : elle vit dans le
meme dossier qu'eux et pointe vers eux en relatif. Noms de fichiers, tailles et
empreintes SHA-256 sont lus sur les fichiers presents — jamais saisis a la main,
pour qu'ils ne puissent pas diverger apres un rebuild.

Une plateforme absente du dossier est simplement omise de la page, ce qui permet
de la generer avant que les deux builds soient disponibles.

    python3 scripts/genera-istruzioni.py "dist/Atex Italia Meeting 0.1.0"
"""

import base64
import hashlib
import html
import io
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
LOGO = RACINE / "brand" / "atex-italia-logo-nero.png"

ARANCIO = "#F99B33"  # l'orange de l'hexagone Atex


def empreinte(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def poids(chemin: Path) -> str:
    mo = chemin.stat().st_size / 1_000_000
    return f"{mo:.0f} MB" if mo >= 10 else f"{mo:.1f} MB"


def logo_base64(largeur: int = 400) -> str:
    """Logo encode en base64, pour que la page reste un fichier autonome."""
    from PIL import Image

    im = Image.open(LOGO).convert("RGBA")
    im = im.resize((largeur, round(im.height * largeur / im.width)), Image.LANCZOS)
    tampon = io.BytesIO()
    im.save(tampon, format="PNG", optimize=True)
    return base64.b64encode(tampon.getvalue()).decode()


def trouver(dossier: Path, suffixe: str):
    trouves = sorted(dossier.glob(f"*{suffixe}"))
    return trouves[0] if trouves else None


def lien(chemin: Path) -> str:
    """Lien relatif : la page est servie depuis le meme dossier."""
    return html.escape(chemin.name.replace(" ", "%20"))


def construire(dossier: Path) -> str:
    dmg = trouver(dossier, ".dmg")
    exe = trouver(dossier, ".exe")
    msi = trouver(dossier, ".msi")

    if not (dmg or exe):
        raise SystemExit(f"Aucun installeur trouve dans {dossier}")

    cartes = []
    if dmg:
        cartes.append(f'''      <a class="scelta" href="{lien(dmg)}">
        <span class="sistema">macOS</span>
        <span class="dettaglio">Mac Apple Silicon (M1 e successivi)</span>
        <span class="peso">Scarica il .dmg &mdash; {poids(dmg)}</span>
      </a>''')
    if exe:
        cartes.append(f'''      <a class="scelta" href="{lien(exe)}">
        <span class="sistema">Windows</span>
        <span class="dettaglio">Windows 10 e 11, 64 bit</span>
        <span class="peso">Scarica il .exe &mdash; {poids(exe)}</span>
      </a>''')

    secondaire = ""
    if msi:
        secondaire = (
            f'  <p class="secondario">Per l&rsquo;installazione centralizzata via GPO esiste anche il\n'
            f'     <a href="{lien(msi)}">pacchetto .msi</a> ({poids(msi)}) &mdash; riservato all&rsquo;IT.</p>\n'
        )

    sezioni = []
    if dmg:
        sezioni.append('''  <h3>macOS</h3>
  <ol>
    <li>Aprire il file <span class="file">.dmg</span> con un doppio clic.</li>
    <li>Trascinare <strong>Atex Italia Meeting</strong> sulla cartella <em>Applicazioni</em>.</li>
    <li>Aprire l&rsquo;app dalla cartella Applicazioni.</li>
  </ol>
  <p><strong>Al primo avvio macOS blocca l&rsquo;app.</strong> &Egrave; normale : l&rsquo;applicazione
     &egrave; interna e non &egrave; firmata con un certificato Apple. Per sbloccarla, una volta sola :</p>
  <ol>
    <li>Fare un primo doppio clic sull&rsquo;app &mdash; comparir&agrave; un avviso, chiuderlo.</li>
    <li>Aprire <strong>Impostazioni di Sistema &rarr; Privacy e Sicurezza</strong>.</li>
    <li>Scorrere fino in fondo alla pagina e cliccare su <strong>&laquo; Apri comunque &raquo;</strong>.</li>
  </ol>
  <p>In alternativa, un solo comando da incollare nel Terminale :</p>
  <pre><code>xattr -dr com.apple.quarantine "/Applications/Atex Italia Meeting.app"</code></pre>''')
    if exe:
        sezioni.append('''  <h3>Windows</h3>
  <ol>
    <li>Aprire il file <span class="file">.exe</span> con un doppio clic.</li>
    <li><strong>Comparir&agrave; &laquo; Windows ha protetto il PC &raquo;.</strong> &Egrave; normale, per lo
        stesso motivo : cliccare su <strong>&laquo; Ulteriori informazioni &raquo;</strong>, poi su
        <strong>&laquo; Esegui comunque &raquo;</strong>.</li>
    <li>Seguire l&rsquo;installazione. Non servono diritti di amministratore.</li>
  </ol>''')

    empreintes = "\n".join(
        f'    <p class="impronta"><b>SHA-256 &mdash; {html.escape(f.suffix)}</b><br>{empreinte(f)}</p>'
        for f in (dmg, exe, msi) if f
    )

    return f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atex Italia Meeting &mdash; Installazione</title>
<style>
  :root {{
    --arancio: {ARANCIO};
    --testo: #1a1a1a;
    --tenue: #666;
    --bordo: #e4e4e7;
    --sfondo: #fff;
    --riquadro: #f7f7f8;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --testo: #ededed; --tenue: #a1a1a6; --bordo: #2e2e32;
      --sfondo: #141416; --riquadro: #1d1d20;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 3rem 1.5rem 5rem;
    background: var(--sfondo); color: var(--testo);
    font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  main {{ max-width: 42rem; margin: 0 auto; }}
  header {{ border-bottom: 1px solid var(--bordo); padding-bottom: 1.75rem; margin-bottom: 2.5rem; }}
  .marchio {{ display: block; width: 200px; height: auto; margin-bottom: 1.5rem; }}
  @media (prefers-color-scheme: dark) {{
    /* Il lettering e nero : su fondo scuro lo si inverte in bianco. */
    .marchio {{ filter: invert(1) hue-rotate(180deg); }}
  }}
  h1 {{ font-size: 1.75rem; letter-spacing: -.02em; margin: 0 0 .35rem; }}
  .sottotitolo {{ color: var(--tenue); margin: 0; }}
  h2 {{ font-size: 1.1rem; margin: 2.5rem 0 .85rem; letter-spacing: -.01em; }}
  h3 {{ font-size: .95rem; margin: 1.75rem 0 .6rem; letter-spacing: -.01em; }}
  ol, ul {{ padding-left: 1.35rem; }}
  li {{ margin-bottom: .6rem; }}
  code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .875em; background: var(--riquadro);
    padding: .15em .4em; border-radius: 4px;
  }}
  pre {{
    background: var(--riquadro); border: 1px solid var(--bordo);
    border-radius: 8px; padding: .9rem 1rem; overflow-x: auto;
  }}
  pre code {{ background: none; padding: 0; }}
  .nota {{
    border-left: 3px solid var(--arancio); background: var(--riquadro);
    padding: .9rem 1.1rem; border-radius: 0 8px 8px 0; margin: 1.5rem 0;
  }}
  .nota p {{ margin: 0; }}
  .file {{
    display: inline-block; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .9rem; font-weight: 600;
  }}
  .scarica {{ display: grid; gap: .85rem; margin: 0 0 .5rem; }}
  @media (min-width: 34rem) {{ .scarica {{ grid-template-columns: repeat({len(cartes)}, 1fr); }} }}
  .scelta {{
    display: block; text-decoration: none; color: inherit;
    border: 1px solid var(--bordo); border-radius: 10px;
    padding: 1.1rem 1.2rem; background: var(--riquadro);
    transition: border-color .15s ease, transform .15s ease;
  }}
  .scelta:hover {{ border-color: var(--arancio); transform: translateY(-1px); }}
  .scelta .sistema {{ display: block; font-weight: 600; font-size: 1.05rem; margin-bottom: .15rem; }}
  .scelta .dettaglio {{ display: block; color: var(--tenue); font-size: .85rem; }}
  .scelta .peso {{
    display: inline-block; margin-top: .7rem; color: var(--arancio);
    font-weight: 600; font-size: .85rem;
  }}
  .secondario {{ font-size: .85rem; color: var(--tenue); margin-top: .35rem; }}
  .secondario a {{ color: var(--tenue); }}
  footer {{
    margin-top: 3.5rem; padding-top: 1.5rem; border-top: 1px solid var(--bordo);
    color: var(--tenue); font-size: .85rem;
  }}
  .impronta {{ word-break: break-all; font-size: .78rem; color: var(--tenue); margin: .3rem 0; }}
</style>
</head>
<body>
<main>
  <header>
    <img class="marchio" src="data:image/png;base64,{logo_base64()}" alt="Atex Italia">
    <h1>Atex Italia Meeting</h1>
    <p class="sottotitolo">Versione 0.1.0 &mdash; appunti di riunione, trascrizione e riassunti, tutto in locale.</p>
  </header>

  <h2>Scaricare</h2>
  <div class="scarica">
{chr(10).join(cartes)}
  </div>
{secondaire}
  <div class="nota">
    <p>Su un <strong>Mac Intel</strong> l&rsquo;app non si avvia : serve una versione
       compilata a parte. Chiedere a Mohamet Ba.</p>
  </div>

  <h2>Installazione</h2>
{chr(10).join(sezioni)}

  <h2>Cosa succede la prima volta che si usa</h2>
  <p>L&rsquo;app chiede l&rsquo;accesso al <strong>microfono</strong> e alla
     <strong>registrazione dello schermo</strong> &mdash; quest&rsquo;ultima serve a catturare
     l&rsquo;audio delle videoconferenze, senza non si sente l&rsquo;interlocutore.</p>
  <p>Poi scarica i propri modelli di intelligenza artificiale : diverse centinaia
     di MB, una sola volta. Meglio farlo su una connessione stabile.</p>

  <h2>Dove finiscono i dati</h2>
  <ul>
    <li>Registrazioni, trascrizioni e riassunti restano in un database
        <strong>sul computer</strong>. Non vengono inviati da nessuna parte.</li>
    <li>Nessuna telemetria : l&rsquo;app non riporta nulla a nessuno.</li>
    <li>Nessun collegamento con il CRM : ogni verbale resta sul computer di chi
        l&rsquo;ha registrato. L&rsquo;esportazione si fa manualmente dall&rsquo;app.</li>
    <li>Nessun aggiornamento automatico : le nuove versioni verranno distribuite
        come questa.</li>
  </ul>

  <h2>Problemi</h2>
  <p>Per qualsiasi difficolt&agrave;, scrivere a Mohamet Ba.</p>

  <footer>
{empreintes}
    <p style="margin-top:1rem">Basato su Meetily (licenza MIT) &copy; Zackriya Solutions.</p>
  </footer>
</main>
</body>
</html>
'''


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    dossier = Path(sys.argv[1])
    if not dossier.is_dir():
        raise SystemExit(f"Dossier introuvable : {dossier}")

    page = construire(dossier)
    sortie = dossier / "ISTRUZIONI.html"
    sortie.write_text(page, encoding="utf-8")

    print(f"{sortie} ({len(page) // 1024} Ko)")
    for f in sorted(dossier.iterdir()):
        if f.suffix in (".dmg", ".exe", ".msi"):
            print(f"  {f.name:<48} {poids(f):>8}  {empreinte(f)[:16]}...")


if __name__ == "__main__":
    main()
