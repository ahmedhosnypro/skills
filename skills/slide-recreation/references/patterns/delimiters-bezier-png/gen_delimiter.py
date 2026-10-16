#!/usr/bin/env python3
"""Pattern: delimiters-bezier-png — generator.

Renders ONE smooth quadratic-Bézier centerline stroke per delimiter (a tall near-
round paren) at 600 dpi on a transparent canvas, tight-cropped, and writes a JSON
sidecar with the exact ink bbox. The companion example.js embeds it at EXACT size.

This is the certified construction for smooth curved delimiters — use instead of
font-glyph parens (garbage doubled caps) and ARC shape presets (LibreOffice renders
them as double parallel strokes with merged caps — measured).

Usage:
  python3 gen_delimiter.py <lp|rp> <span_pt> <stroke_pt> <hex_color> <out.png>

  lp / rp    which side (controls which edge the bulge lands on)
  span_pt    vertical ink span of the delimiter (topmost enclosed line top
             minus pad  -> bottommost line bottom plus pad, incl. descenders)
  stroke_pt  stroke width S; ink depth beyond the bulge D=2.5pt, PAD=0.5pt
             (full ink span bulge->tip = S + D + AA)

LAWS carried by the sidecar/embed contract (see example.js):
 - addImage at EXACT w = px/600 in; NEVER rescale (a vertical-only stretch keeps
   the hairline; horizontal rescale blurs it).
 - anchor: side "lp" lands the ink LEFT edge on the measured stroke column;
   "rp" lands the ink RIGHT edge; y so ink_top == measured block top.
 - INK-STRENGTH HIERARCHY: a stroke whose window has ZERO sub-170-luminance px
   was genuinely faint paint in the source, not JPEG erosion — faint strokes
   get the measured light color; solid strokes get the solid color. Adjudicate
   "too light/heavy" vision claims against same-frame control digits.
 - FAINT-PAINT TRAP: a faint stroke's visible extent is shorter than its true
   extent (JPEG erodes faint tips) — rescan the original at looser thresholds
   (lum < 225) before believing a "too short" claim.
 - THRESHOLD-GEOMETRY: never compare ink px-counts between a 1px=1pt JPEG and
   a 150dpi render at the same threshold (AA profiles differ by scale) — use
   luminance transects + coverage reasoning, convert with the calibrated scale.
 - Measure stroke waist in the inter-line gap band (cap-bottom+AA -> next line
   top) and spans in tip bands clear of enclosed text.
"""
import json
import sys

from PIL import Image, ImageDraw

DPI = 600
BULGE_DEPTH = 2.5   # pt of stroke depth beyond the bulge edge
PAD = 0.5           # pt padding around the stroke in the canvas


def gen(side: str, span_pt: float, stroke_pt: float, hex_color: str, out: str) -> None:
    span = span_pt / 72 * DPI
    depth = (stroke_pt + BULGE_DEPTH + 1.0) / 72 * DPI   # +1pt AA allowance
    pad = PAD / 72 * DPI
    W, H = int(depth + 2 * pad), int(span + 2 * pad)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lw = stroke_pt / 72 * DPI

    # quadratic Bézier: tip(top) -> bulge(mid) -> tip(bottom)
    x_tip = pad if side == "lp" else W - pad
    x_bulge = W - pad if side == "lp" else pad
    cx = (x_tip + x_bulge) / 2
    steps = 200
    pts = []
    for i in range(steps + 1):
        t = i / steps
        # quadratic interpolation tip -> bulge -> tip
        x = (1 - t) ** 2 * x_tip + 2 * (1 - t) * t * cx + t ** 2 * x_tip
        # ease the bulge reach by the curve parameter (max at mid)
        pts.append((x, pad + t * span))
    d.line(pts, fill=tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4)) + (255,),
           width=int(lw), joint="curve")

    # tight-crop to ink
    bbox = img.getbbox()
    img = img.crop(bbox)
    img.save(out)
    sidecar = {
        "image": out,
        "px_w": img.size[0], "px_h": img.size[1],
        "w_in": img.size[0] / DPI, "h_in": img.size[1] / DPI,
        "stroke_pt": stroke_pt, "color": hex_color, "side": side,
    }
    with open(out.rsplit(".", 1)[0] + ".json", "w") as f:
        json.dump(sidecar, f, indent=1)
    print(json.dumps(sidecar))


if __name__ == "__main__":
    side, span, stroke, color, out = sys.argv[1:6]
    gen(side, float(span), float(stroke), color, out)
