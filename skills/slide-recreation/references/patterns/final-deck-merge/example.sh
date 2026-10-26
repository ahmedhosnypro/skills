#!/usr/bin/env bash
# Pattern: final-deck-merge
# Combine the per-slide decks into one all-in-one file as a BYTE-VERBATIM OPC
# merge — never rebuild or re-encode the certified content.
#
# CONTINUOUS DOCTRINE: the combined deck is a
# continuous artifact. MODE=placeholder initializes it at APPROVAL time — N
# pages (one per confirmed frame, printed-badge order), each page the original
# frame image full-bleed. MODE=update <N> replaces page N with the certified
# slide N's package content at the OPC level (same verbatim laws as the full
# merge; media renamed per slide; rels retargeted). A state ledger
# (final_deck_state.json) records per-page placeholder|certified + source
# md5s. The example below is the CLOSE-TIME gate: run it once the last page is
# replaced — page N vs source N must still be 0-mismatch.
#
# LAWS:
# - Merge at the package level: copy each source slide's XML VERBATIM (slide
#   rels are per-part, so rIds never collide across slides — only the .rels
#   targets need retargeting: shared layout, per-slide notes copy, media
#   renamed per slide like imgNNN_<orig>). Media file names collide across
#   decks — always rename per slide.
# - Skeleton parts (master/layout/theme) must be byte-identical across sources
#   (md5-check); a source saved by a different toolchain may carry its own
#   master chain — its slide must be self-contained (own bg, explicit fonts)
#   and the render gate decides.
# - Presentation.xml/rels + [Content_Types].xml rebuilt for N slides
#   (sldId ids 256.., slide rels, per-slide Overrides).
# - GATE: render the merged deck AND every source deck in ONE soffice session
#   (same profile), pixel-diff page N vs source N — 0/N mismatches required.
#   Bulk render QA runs under PROJECT scratch, never /tmp (tmpfs ENOSPC).
set -euo pipefail

# ---- parameters -----------------------------------------------------------------
PPTX_DIR=$1        # directory of per-slide decks (one per slide, plain names)
OUT=$2             # the combined deck path
MERGER=${MERGER:-"python3 merge_final_deck.py"}   # your OPC merge script
N=${N:-64}

# ---- merge ------------------------------------------------------------------------
$MERGER "$PPTX_DIR" "$OUT"

# ---- gate: render merged + all sources, pixel-diff page N vs source N --------------
V="$PPTX_DIR/.merge_gate"; rm -rf "$V"; mkdir -p "$V/src" "$V/pages" "$V/src_png"
soffice --headless -env:UserInstallation=file://"$V/lo" --convert-to pdf --outdir "$V" "$OUT" >/dev/null
pdfinfo "$V/$(basename "${OUT%.pptx}").pdf" | grep -q "Pages: *$N" || { echo "FAIL: page count"; exit 1; }
for f in "$PPTX_DIR"/slide_*_recreated.pptx; do
  soffice --headless -env:UserInstallation=file://"$V/lo" --convert-to pdf --outdir "$V/src" "$f" >/dev/null
done
pdftoppm -png -r 150 "$V/$(basename "${OUT%.pptx}").pdf" "$V/pages/pg"
i=0
for f in "$PPTX_DIR"/slide_*_recreated.pptx; do
  i=$((i+1)); pdftoppm -png -r 150 "$V/src/$(basename "${f%.pptx}").pdf" "$V/src_png/s$(printf %03d $i)"
done
python3 - "$V" <<'EOF'
import sys
from PIL import Image, ImageChops
v = sys.argv[1]
bad = []
for n in range(1, 65):
    a = Image.open(f"{v}/pages/pg-{n:02d}.png").convert("RGB")
    b = Image.open(f"{v}/src_png/s{n:03d}-1.png").convert("RGB")
    if a.size != b.size or ImageChops.difference(a, b).getbbox():
        bad.append(n)
print("mismatched pages:", bad if bad else "NONE — 0/64, merge is lossless")
sys.exit(1 if bad else 0)
EOF
rm -rf "$V/src_png" "$V/src"   # keep the render pdf + report if desired
