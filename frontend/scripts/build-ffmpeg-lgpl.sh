#!/bin/bash
# Compile un ffmpeg minimal et redistribuable pour le sidecar de Maffioletti Meet.
#
# POURQUOI : le paquet npm `ffmpeg-static` livre un binaire compile en
# `--enable-gpl --enable-nonfree`, combinaison juridiquement non redistribuable.
# L'app n'a besoin que d'encoder en AAC (encodeur natif) et de decoder de
# l'audio courant : aucun composant GPL n'est necessaire.
#
# CE QU'ON OBTIENT : un binaire statique LGPL v2.1, sans aucune dependance
# externe (--disable-autodetect garantit qu'il n'attrape pas les bibliotheques
# de Homebrew), et sans pile reseau (--disable-network) — ffmpeg ne peut donc
# pas ouvrir d'URL, ce qui va dans le sens d'une app 100 % locale.
#
# CONFORMITE LGPL : conserver ce script et la version ci-dessous. Ils suffisent
# a reconstruire le binaire a l'identique depuis les sources publiques d'ffmpeg,
# ce qui est ce que la licence exige de fournir.
#
# Usage : ./scripts/build-ffmpeg-lgpl.sh [dossier-de-travail]

set -euo pipefail

FFMPEG_VERSION="7.1.1"
WORKDIR="${1:-${TMPDIR:-/tmp}/ffmpeg-lgpl-build}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$SCRIPT_DIR/../src-tauri/vendor/ffmpeg"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

TARBALL="ffmpeg-$FFMPEG_VERSION.tar.xz"
if [ ! -f "$TARBALL" ]; then
  echo "Telechargement des sources ffmpeg $FFMPEG_VERSION..."
  curl -fL --proto '=https' --tlsv1.2 -o "$TARBALL" \
    "https://ffmpeg.org/releases/$TARBALL"
fi

rm -rf "ffmpeg-$FFMPEG_VERSION"
tar xf "$TARBALL"
cd "ffmpeg-$FFMPEG_VERSION"

echo "Configuration (LGPL v2.1, statique, sans reseau)..."
./configure \
  --prefix=/usr/local \
  --disable-autodetect \
  --disable-gpl \
  --disable-nonfree \
  --disable-version3 \
  --disable-network \
  --disable-shared \
  --enable-static \
  --disable-programs \
  --enable-ffmpeg \
  --disable-doc \
  --disable-debug \
  --enable-pthreads
# NB : --prefix n'est jamais utilise (on ne fait pas `make install`), mais il
# apparait dans la ligne de configuration affichee par `ffmpeg -version`.
# On le fixe pour que cette ligne reste lisible et reproductible.

echo "Compilation..."
make -j"$(sysctl -n hw.ncpu)"

# Tauri attend le binaire suffixe par le target triple de rustc
# (aarch64-apple-darwin), pas par `uname -m` (arm64).
TRIPLE="$(rustc -vV | awk '/^host:/ {print $2}')"
if [ -z "$TRIPLE" ]; then
  echo "rustc introuvable : impossible de determiner le target triple." >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
cp ffmpeg "$DEST_DIR/ffmpeg-$TRIPLE"
strip "$DEST_DIR/ffmpeg-$TRIPLE" || true

echo ""
echo "Binaire : $DEST_DIR/ffmpeg-$TRIPLE"
"$DEST_DIR/ffmpeg-$TRIPLE" -version | head -2
