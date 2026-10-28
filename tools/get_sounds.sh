#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Fetches the clip player's sounds once: FluidR3 GM (Frank Wen, MIT license), from Ubuntu's fluid-soundfont-gm
# package, into sounds/ (gitignored, 142 MB). No root needed. After this the player works offline.
set -e
cd "$(dirname "$0")/.."
# Also GeneralUser GS v2.0.3 (S. Christian Collins, free for any music making; the sounds A/B, Oct 28), 32 MB.
GU=https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/684543d5e5efaef08d02be50dcda8d552478fa60
mkdir -p sounds
[ -f sounds/GeneralUser-GS.sf2 ] || { curl -sfL -o sounds/GeneralUser-GS.sf2 "$GU/GeneralUser-GS.sf2" &&
  curl -sfL -o sounds/GeneralUser-GS.license.txt "$GU/documentation/LICENSE.txt" && echo "sounds/GeneralUser-GS.sf2 ready"; }
[ -f sounds/FluidR3_GM.sf2 ] && { echo "sounds/FluidR3_GM.sf2 is already here"; exit 0; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
(cd "$tmp" && apt-get download fluid-soundfont-gm && dpkg-deb -x fluid-soundfont-gm_*.deb x)
mkdir -p sounds
cp "$tmp/x/usr/share/sounds/sf2/FluidR3_GM.sf2" sounds/
cp "$tmp/x/usr/share/doc/fluid-soundfont-gm/copyright" sounds/FluidR3_GM.copyright
echo "sounds/FluidR3_GM.sf2 ready"
