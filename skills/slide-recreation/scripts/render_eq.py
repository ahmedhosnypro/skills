#!/usr/bin/env python3
"""Render a LaTeX (mathtext) equation to a tight transparent PNG with baseline metadata.
Usage: python3 render_eq.py '<latex>' out.png <fontsize_pt> <hexcolor> [--bg RRGGBB]
Prints JSON: {path,w_px,h_px,w_in,h_in,baseline_px,baseline_frac,dpi,fontsize_pt,color}
Contract: place in pptxgenjs with w=w_in, h=h_in -> glyphs are exactly fontsize pt on the slide.
baseline_frac*h_in = inches from image TOP down to the math baseline.
"""
import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

DPI = 600      # 4x the 150dpi QA render -> clean downsampling
PAD_PX = 8

def render(latex, out, fontsize, color, bg=None):
    fig = plt.figure(figsize=(10, 4), dpi=DPI)
    fig.patch.set_alpha(0.0 if bg is None else 1.0)
    if bg is not None:
        fig.patch.set_facecolor("#" + bg.lstrip("#"))
    # 'x' probe shares the equation's baseline (va='baseline'); 'x' sits flat on it
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
    baseline_row = int(np.where(ink[:, px0:px1].any(axis=1))[0][-1])  # x ink bottom = baseline
    ink[:, :px1 + 20] = False                                        # drop the probe
    rows = np.where(ink.any(axis=1))[0]; cols = np.where(ink.any(axis=0))[0]
    if len(rows) == 0:
        raise SystemExit(f"no ink for {latex!r} (mathtext parse error?)")
    y0, y1 = max(rows[0]-PAD_PX, 0), min(rows[-1]+PAD_PX, buf.shape[0])
    x0, x1 = max(cols[0]-PAD_PX, 0), min(cols[-1]+PAD_PX, buf.shape[1])
    Image.fromarray(buf[y0:y1, x0:x1]).save(out)   # RGBA, transparent bg
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
