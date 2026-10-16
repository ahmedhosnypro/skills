#!/usr/bin/env python3
"""Closed-loop containment checker for the inner-frame-budget pattern.

Renders a single-slide pptx via a private soffice profile, then PIL-asserts:
  frame mode: no content ink in the BAND just outside each frame edge
              (band width = 0.06in, starting just past the frame stroke) —
              catches content that crosses or touches the frame line.
  gap   mode: a gap band (e.g. between an image edge and a caption) must be
              pure background — catches z-order masking of frame crossings.

Usage (all geometry in inches, 150 dpi render):
  python3 check_containment.py <deck.pptx> frame <fx> <fy> <fw> <fh>
  python3 check_containment.py <deck.pptx> gap   <x0> <y0> <x1> <y1>
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

DPI = 150.075
BAND = 0.06  # inches of no-ink zone beyond each frame edge


def render(pptx: str) -> str:
    tmp = tempfile.mkdtemp(prefix="contain_")
    subprocess.run(
        ["soffice", "--headless",
         "-env:UserInstallation=file://" + os.path.join(tmp, "lo"),
         "--convert-to", "pdf", "--outdir", tmp, pptx],
        check=True, capture_output=True, timeout=300)
    pdf = os.path.join(tmp, os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
    out = os.path.join(tmp, "page")
    subprocess.run(["pdftoppm", "-png", "-r", "150", pdf, out],
                   check=True, timeout=300)
    return out + "-1.png"


def ink(img: Image.Image) -> np.ndarray:
    """True where a pixel is NOT near the light-gray slide background."""
    a = np.asarray(img.convert("RGB")).astype(int)
    return np.abs(a - np.array([232, 232, 232])).sum(axis=2) > 40


def px(v: float) -> int:
    return int(round(v * DPI))


def main() -> None:
    pptx, mode = sys.argv[1], sys.argv[2]
    vals = [float(v) for v in sys.argv[3:7]]
    m = ink(Image.open(render(pptx)))
    ok = True
    if mode == "frame":
        fx, fy, fw, fh = vals
        x0, y0, x1, y1 = px(fx), px(fy), px(fx + fw), px(fy + fh)
        b = px(BAND)
        # bands immediately outside each frame edge (skip the stroke itself: +-3px)
        bands = {
            "top":    m[y0 - b:y0 - 3, x0 + 3:x1 - 3],
            "bottom": m[y1 + 3:y1 + b, x0 + 3:x1 - 3],
            "left":   m[y0 + 3:y1 - 3, x0 - b:x0 - 3],
            "right":  m[y0 + 3:y1 - 3, x1 + 3:x1 + b],
        }
        bad = {k: int(v.sum()) for k, v in bands.items()}
        ok = all(v == 0 for v in bad.values())
        print(f"frame=({fx},{fy},{fw},{fh})in  ink-px in outside bands: {bad}")
    elif mode == "gap":
        gx0, gy0, gx1, gy1 = vals
        n = int(m[px(gy0):px(gy1), px(gx0):px(gx1)].sum())
        print(f"gap band ({gx0},{gy0})-({gx1},{gy1})in: non-background px={n} (want 0)")
        ok = n == 0
    else:
        sys.exit(f"unknown mode {mode}")
    print("CONTAINMENT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
