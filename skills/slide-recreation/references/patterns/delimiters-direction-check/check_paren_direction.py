#!/usr/bin/env python3
"""Pattern: delimiters-direction-check — closed-loop delimiter direction check.

Middle-band extremum test, per tall thin ink stroke: in the middle third of the
stroke's ink-row span, a '(' has its extreme ink on the LEFT of its full span
(belly outer-left, cusps inner-right); a ')' has it on the RIGHT (mirrored).
One bow-direction template reused for both sides renders a MIRRORED pair — a
defect that ships silently through full-slide judges at hairline widths.

Run on EVERY hand-drawn delimiter asset after generation, and on the matching
crop of the 150dpi render (closed loop) and of the original frame (ground
truth). A judge PASS never waives this check.

usage:
  python3 check_paren_direction.py <image> [image ...]
      [--min-rows-frac F]   stroke must span >= F of image height (default 0.25)
      [--lum-threshold T]   ink threshold for opaque images (default 200)
      [--expect "x0:x1=(,x2:x3=)"]  explicit windows + expected shapes instead
                                    of auto-pairing (use for brackets etc.)

exit 0 = every checked stroke matches its expected shape;
exit 1 = any mirrored or unresolved stroke (fail loud — rebuild the asset).
"""
import sys
import numpy as np
from PIL import Image


def load_ink(path, lum_threshold):
    im = Image.open(path)
    if im.mode == "RGBA" or (im.mode == "LA"):
        a = np.array(im.convert("RGBA"))[:, :, 3]
        return a > 64, "alpha"
    a = np.array(im.convert("L")).astype(float)
    return a < lum_threshold, "luminance"


def stroke_shape(ink, cx0, cx1, min_rows_frac):
    """Classify one tall thin stroke at columns [cx0..cx1]."""
    H = ink.shape[0]
    win = ink[:, cx0:cx1 + 1]
    rows = np.where(win.any(axis=1))[0]
    if len(rows) == 0:
        return None, "no ink"
    # longest contiguous run = the delimiter stroke itself
    runs, s = [], rows[0]
    for i in range(1, len(rows)):
        if rows[i] != rows[i - 1] + 1:
            runs.append((s, rows[i - 1]))
            s = rows[i]
    runs.append((s, rows[-1]))
    r0, r1 = max(runs, key=lambda t: t[1] - t[0])
    if r1 - r0 < min_rows_frac * H:
        return None, f"span {r1-r0} < {min_rows_frac:.2f}*H"
    span = r1 - r0
    mid0, mid1 = r0 + span // 3, r0 + 2 * span // 3
    # horizontal-bar rows (e.g. '=' bars) reach past this stroke's columns
    row_maxcol = np.full(H, -1)
    for y in range(H):
        cols = np.where(win[y])[0]
        if len(cols):
            row_maxcol[y] = cols.max()
    bar = set(np.where(row_maxcol > (cx1 - cx0) + 6)[0])
    belly_rows = [y for y in range(mid0, mid1 + 1) if y not in bar and win[y].any()]
    tip_rows = [y for y in list(range(r0, r0 + 4)) + list(range(max(r1 - 3, r0), r1 + 1))
                if y not in bar and win[y].any()]
    if not belly_rows or not tip_rows:
        return None, "unresolved (bar overlap)"
    bx = float(np.mean([np.where(win[y])[0].mean() for y in belly_rows])) + cx0
    tx = float(np.mean([np.where(win[y])[0].mean() for y in tip_rows])) + cx0
    if tx > bx + 1.0:
        return "(", f"belly {bx:.1f} tips {tx:.1f}"
    if tx < bx - 1.0:
        return ")", f"belly {bx:.1f} tips {tx:.1f}"
    return "STRAIGHT", f"belly {bx:.1f} tips {tx:.1f}"


def check(path, min_rows_frac, lum_threshold, expects):
    ink, _ = load_ink(path, lum_threshold)
    H, W = ink.shape
    strokes = []
    if expects:
        for item in expects.split(","):
            win, want = item.split("=")
            x0, x1 = (int(v) for v in win.split(":"))
            shape, why = stroke_shape(ink, x0, x1, min_rows_frac)
            strokes.append((f"x[{x0}..{x1}]", shape, want, why))
    else:
        colcount = ink.sum(axis=0)
        tall = np.where(colcount >= min_rows_frac * H)[0]
        if len(tall) == 0:
            print(f"{path}: NO tall thin strokes found (min_rows_frac={min_rows_frac})")
            return False
        clusters, start = [], tall[0]
        for i in range(1, len(tall)):
            if tall[i] != tall[i - 1] + 1:
                clusters.append((start, tall[i - 1]))
                start = tall[i]
        clusters.append((start, tall[-1]))
        clusters = [c for c in clusters if c[1] - c[0] <= 80]  # thin strokes only
        if len(clusters) != 2:
            print(f"{path}: {len(clusters)} thin tall clusters (need exactly 2 for "
                  f"auto-pairing; other ink — glyphs, ellipses, bars — also qualifies). "
                  f"Pass --expect \"x0:x1=(,x2:x3=)\" with the measured delimiter columns.")
            return False
        (a0, a1), (b0, b1) = clusters
        sa, wa = stroke_shape(ink, a0, a1, min_rows_frac)
        sb, wb = stroke_shape(ink, b0, b1, min_rows_frac)
        strokes.append((f"x[{a0}..{a1}]", sa, "(", wa))
        strokes.append((f"x[{b0}..{b1}]", sb, ")", wb))
    ok = True
    for tag, shape, want, why in strokes:
        good = shape == want
        ok &= good
        print(f"{path} {tag}: measured={shape} expected={want} ({why})"
              f"{'' if good else '  <-- MIRRORED/UNRESOLVED'}")
    return ok


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    min_frac, lum, expect = 0.25, 200, None
    files = []
    i = 0
    while i < len(args):
        if args[i] == "--min-rows-frac":
            min_frac = float(args[i + 1]); i += 2
        elif args[i] == "--lum-threshold":
            lum = float(args[i + 1]); i += 2
        elif args[i] == "--expect":
            expect = args[i + 1]; i += 2
        else:
            files.append(args[i]); i += 1
    allok = True
    for f in files:
        allok = check(f, min_frac, lum, expect) and allok
    print(f"PAREN-DIRECTION: {'PASS' if allok else 'FAIL'}")
    sys.exit(0 if allok else 1)
