#!/usr/bin/env python3
"""Closed-loop alignment checker for the equations-mathtext-png pattern.

Renders the pptx at 150 dpi and asserts the equation ink band matches the
expected region (from the ORIGINAL's PIL-measured ink edges, converted to the
150dpi space with px = in x 150.075) within tolerance.

Usage:
  python3 align_check.py <deck.pptx> <x0> <y0> <x1> <y1>   # expected ink band, inches
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

DPI = 150.075
TOL = 4  # px at 150 dpi


def render(pptx: str) -> str:
    tmp = tempfile.mkdtemp(prefix="eqchk_")
    subprocess.run(["soffice", "--headless",
                    "-env:UserInstallation=file://" + os.path.join(tmp, "lo"),
                    "--convert-to", "pdf", "--outdir", tmp, pptx],
                   check=True, capture_output=True, timeout=300)
    pdf = os.path.join(tmp, os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
    out = os.path.join(tmp, "page")
    subprocess.run(["pdftoppm", "-png", "-r", "150", pdf, out],
                   check=True, timeout=300)
    return out + "-1.png"


def ink(img: Image.Image) -> np.ndarray:
    a = np.asarray(img.convert("RGB")).astype(int)
    return np.abs(a - np.array([232, 232, 232])).sum(axis=2) > 40


def main() -> None:
    pptx = sys.argv[1]
    x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
    m = ink(Image.open(render(pptx)))
    region = m[int(y0 * DPI) - 30:int(y1 * DPI) + 30,
               int(x0 * DPI) - 30:int(x1 * DPI) + 30]
    ys, xs = np.where(region)
    if len(xs) == 0:
        print("ALIGNMENT: FAIL — no equation ink in the expected region")
        sys.exit(1)
    got = (xs.min() + int(x0 * DPI) - 30, ys.min() + int(y0 * DPI) - 30,
           xs.max() + int(x0 * DPI) - 30, ys.max() + int(y0 * DPI) - 30)
    want = (int(x0 * DPI), int(y0 * DPI), int(x1 * DPI), int(y1 * DPI))
    deltas = [abs(g - w) for g, w in zip(got, want)]
    ok = all(d <= TOL for d in deltas)
    print(f"want (px): {want}\ngot  (px): {got}\ndeltas:   {deltas}")
    print("ALIGNMENT:", "PASS" if ok else "FAIL  (tolerance %dpx)" % TOL)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
