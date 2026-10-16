#!/usr/bin/env bash
# Pattern: dense-region-crop-compare
# Dense/small regions (equations, delimiters, table cells, tight gaps) are
# INVISIBLE at full-slide resolution — the full-slide judge is NOT sufficient
# for them. Run a cropped-pair comparison per dense region BEFORE certifying.
#
# LAWS:
# - Crop the SAME region from both the render and the original (convert the
#   render-space box to original-space with the width ratio); upscale x4-x6 if
#   the crop is < ~400px wide. Tiny crops fabricate geometry and produce
#   contradictory bodies on the same pixels (measured).
# - Run at FULL judge params (thinking high, max-tokens 65536, wide wall) —
#   dense crops need them more than full slides do.
# - PIXEL-MEASURE BOTH CROPS FIRST (mask areas, ink spans) so a fabricated
#   judge body can be rebutted with numbers. A coherent body can still
#   mis-state sizes at zoom: measure the disputed span in BOTH PNGs; a claim
#   contradicted by ~1px centers is a rebuttal, not a fix trigger.
# - Bank every crop transcript next to the numeric rebuttals; a PASS with a
#   measured-rebuttable MINOR note is still a PASS. A body whose numbers are
#   false against the very PNGs it judged is defective evidence: bank it,
#   re-run at better conditioning — never "fix" against made-up numbers.
# - Use the CURRENT judge template extracted programmatically from the
#   instructions file; older banked prompts predate clauses and mislead.
set -euo pipefail

# ---- parameters ------------------------------------------------------------------
RENDER=$1            # 150dpi render png (e.g. 2001x1125 for a 13.33x7.5in slide)
ORIGINAL=$2          # original frame (e.g. 960x540)
CROP_BOX=$3          # "x0,y0,x1,y1" in the RENDER's pixel space
SCALE=${4:-4}        # upscale factor for small crops
OUTDIR=${5:-crops}

mkdir -p "$OUTDIR"

# 1. crop both at the SAME effective scale, upscale, and measure BEFORE any
#    vision call
python3 - "$RENDER" "$ORIGINAL" "$CROP_BOX" "$SCALE" "$OUTDIR" <<'EOF'
import sys
import numpy as np
from PIL import Image

render, original, box, scale, out = sys.argv[1:6]
x0, y0, x1, y1 = map(int, box.split(","))
scale = int(scale)

r_img = Image.open(render)
o_img = Image.open(original)
k = r_img.width / o_img.width          # render px per original px

r = r_img.crop((x0, y0, x1, y1))
r = r.resize((r.width * scale, r.height * scale), Image.LANCZOS)
r.save(f"{out}/crop_render.png")

o = o_img.crop((int(x0 / k), int(y0 / k), int(x1 / k), int(y1 / k)))
o = o.resize((o.width * scale, o.height * scale), Image.LANCZOS)
o.save(f"{out}/crop_original.png")

for name in ("crop_render.png", "crop_original.png"):
    a = np.asarray(Image.open(f"{out}/{name}").convert("L"))
    ink = a < 180
    ys, xs = np.where(ink)
    if len(xs):
        print(f"{name}: size={a.shape[1]}x{a.shape[0]} ink_px={int(ink.sum())} "
              f"span=({xs.min()},{ys.min()})-({xs.max()},{ys.max()})")
    else:
        print(f"{name}: size={a.shape[1]}x{a.shape[0]} NO INK")
EOF

# 2. the comparison (full params; region-scoped --view; template verbatim).
#    Adapt the gate invocation to your project (see judge-invocation pattern).
#    timeout 1700 <your-gate> timeout 1650 python3 analyze_image.py comparison \
#      "$OUTDIR/crop_render.png" "$OUTDIR/crop_original.png" \
#      --view "Dense-region zoom check: <region description + pixel-measured facts
#              to treat as ground truth>" \
#      --thinking high --max-tokens 65536 --timeout 600 --rounds 1 --tries 1 \
#      --transcript "$OUTDIR/cropcmp.txt" -p "$(cat judge_template.txt)"
echo "crops prepared + measured; run the comparison above with your gate"
