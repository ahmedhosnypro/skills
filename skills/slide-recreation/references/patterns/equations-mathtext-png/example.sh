#!/usr/bin/env bash
# Pattern: equations-mathtext-png
# Equations render in PROFESSIONAL 2D FORMAT (stacked fractions with a real
# horizontal bar, large ∑ with limits above/below, spatially aligned sub/sup) —
# never linear text. Mechanism: matplotlib mathtext -> 600dpi transparent PNG ->
# pptxgenjs.addImage at EXACT size.
#
# Run from this directory:
#   bash example.sh        -> demo_eq.png + demo_eq.json + demo_equation.pptx
#
# LAWS:
# - Render: matplotlib mathtext at 600 dpi, tight bbox, transparent bg; the
#   sidecar JSON carries exact px w/h and baseline_frac.
# - Embed at EXACT size: w = px/600 in, h = px/600 in — NEVER rescale (blurs
#   glyphs). Font size and color are baked at render time.
# - ALIGNMENT LAW: y_image = target_baseline_in - baseline_frac * h_image_in.
#   "Center the image on the line" is WRONG for anything taller than the line.
#   Horizontal: place against the ORIGINAL's PIL-measured ink left edge.
# - Closed loop BEFORE judging: render the pptx at 150dpi and PIL-compare the
#   equation's ink band vs the original's measured region (~4px tolerance) —
#   see align_check.py. A judge PASS does not waive this check.
# - \frac renders script-size operands -> use \dfrac for display-size stacks.
# - Wide equations clip at the left edge -> use a wide-canvas renderer variant.
#   Serif originals -> render with the STIX serif mathtext fontset.
# - Bank every generated PNG + sidecar with the build; never delete them.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RENDER_EQ="$HERE/../../../scripts/render_eq.py"   # the skill's certified renderer

# 1. render the equation (demo values; adapt mathtext/pt/color per measurement)
python3 "$RENDER_EQ" '\dfrac{x - \mu}{\sigma} \in \mathbb{R}^D' demo_eq.png 18 '#000000' > demo_eq.json
# -> prints + banks demo_eq.json: {px_w, px_h, w_in, h_in, baseline_frac, ...}

# 2. embed at EXACT size, aligned by the baseline law (demo values)
NODE_PATH="$(npm root -g)" node -e '
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const side = JSON.parse(fs.readFileSync("demo_eq.json"));
const pres = new pptxgen(); pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide(); s.background = { color: "E8E8E8" };
const baselineY = 3.0;                       // the text baseline this equation sits on (in)
const x = 4.0;                               // the ORIGINAL'"'"'s measured ink left edge (in)
const y = baselineY - side.baseline_frac * side.h_in;   // ALIGNMENT LAW
s.addImage({ path: "demo_eq.png", x, y, w: side.w_in, h: side.h_in });  // EXACT size
pres.writeFile({ fileName: "demo_equation.pptx" }).then(() => console.log("wrote demo_equation.pptx"));
'

# 3. closed-loop check (adapt the region to the original'"'"'s measured ink band)
#    python3 align_check.py demo_equation.pptx  <x0> <y0> <x1> <y1>
echo "next: render demo_equation.pptx at 150dpi and run align_check.py on the equation band"
