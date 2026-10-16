#!/usr/bin/env python3
"""render_eq_wide.py — variant of the certified helper
render_eq.py for WIDE equations.

Why this exists (measured on a certified wide-equation rebuild): the base helper
renders on a 10in-wide (6000px @600dpi) canvas with a baseline probe 'x' at x=0.15
(canvas col ~900). A wide equation (~9in / ~5400px of ink at 26pt) centered at
x=0.5 extends left to canvas col ~300, so its left glyphs overlap the probe's
column range. The helper's probe-erase step
(`ink[:, :px1+20] = False` — mask-only, used to compute the trim box) then cuts
the trim origin past the equation's left edge and the saved PNG starts mid-"="
(d(x_i, x_j) lost). Measured on a 4712px-wide banked asset whose leftmost ink
was the tail of the '=' sign.

The ONLY change vs the certified helper: figsize=(20, 4) so the canvas is 12000px
and the probe (col ~1800) can never overlap an equation centered at col 6000.
Font size, dpi, transparent bg, tight trim, baseline sidecar: byte-identical
behavior. Narrow equations are unaffected either way (the scratch-validation
equations never overlapped the probe).

Usage: python3 render_eq_wide.py '<mathtext>' out.png <fontsize_pt> <hexcolor>
"""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

DPI = 600
PAD_PX = 8

def render(latex, out, fontsize, color, bg=None):
    fig = plt.figure(figsize=(20, 4), dpi=DPI)   # <-- only change: 10in -> 20in canvas
    fig.patch.set_alpha(0.0 if bg is None else 1.0)
    if bg is not None:
        fig.patch.set_facecolor("#" + bg.lstrip("#"))
    eq = fig.text(0.5, 0.5, f"${latex}$", fontsize=fontsize, color=color,
                  ha="center", va="baseline")
    probe = fig.text(0.15, 0.5, "x", fontsize=fontsize, color=color,
                     ha="center", va="baseline")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    pb = probe.get_window_extent(renderer=renderer)
    buf = np.asarray(fig.canvas.buffer_rgba())
    if bg is None:
        ink = buf[:, :, 3] > 8
    else:
        lum = buf[:, :, :3].mean(axis=2)
        target = np.array(matplotlib.colors.to_rgb("#" + color.lstrip("#"))).mean() * 255
        ink = np.abs(lum - target) < 60
    px0, px1 = max(int(pb.x0) - 2, 0), int(pb.x1) + 2
    # sanity (wide-canvas fix): erase ONLY the probe's own columns first, then
    # require that no equation ink remains at/left of the probe cut — otherwise the
    # helper's full erase (ink[:, :px1+20]) would eat the equation's left glyphs.
    noProbe = ink.copy()
    noProbe[:, px0:px1 + 1] = False
    left = np.where(noProbe.any(axis=0))[0]
    if left.size and left[0] <= px1 + 20:
        raise SystemExit(
            f"probe overlap: eq ink col {left[0]} <= probe cut {px1 + 20} — widen the canvas")
    baseline_row = int(np.where(ink[:, px0:px1].any(axis=1))[0][-1])
    ink[:, :px1 + 20] = False
    rows = np.where(ink.any(axis=1))[0]; cols = np.where(ink.any(axis=0))[0]
    if len(rows) == 0:
        raise SystemExit(f"no ink for {latex!r} (mathtext parse error?)")
    y0, y1 = max(rows[0]-PAD_PX, 0), min(rows[-1]+PAD_PX, buf.shape[0])
    x0, x1 = max(cols[0]-PAD_PX, 0), min(cols[-1]+PAD_PX, buf.shape[1])
    Image.fromarray(buf[y0:y1, x0:x1]).save(out)
    h = y1 - y0
    info = {"path": out, "w_px": int(x1-x0), "h_px": int(h),
            "w_in": round(float(x1-x0)/DPI, 5), "h_in": round(float(h)/DPI, 5),
            "baseline_px": int(baseline_row - y0),
            "baseline_frac": round(float(baseline_row - y0)/float(h), 5),
            "dpi": DPI, "fontsize_pt": fontsize, "color": color}
    plt.close(fig)
    return info

if __name__ == "__main__":
    latex, out, fs, color = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    bg = sys.argv[sys.argv.index("--bg") + 1] if "--bg" in sys.argv else None
    print(json.dumps(render(latex, out, fs, color, bg)))
