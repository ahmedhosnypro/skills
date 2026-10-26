#!/usr/bin/env python3
"""Pattern: delimiters-straight-bars — closed-loop bar check for matrix/vector
delimiter pairs.

Each expected delimiter is one straight vertical bar (a 1pt-wide rect) at a
measured window. This checker verifies, per window: (a) ink present across the
measured span, (b) STRAIGHTNESS — the per-row ink centroid stays within
--col-tol of the window's modal column for the whole span (a curved paren or a
font glyph drifts out), (c) the ink-row span matches the measurement, and (d)
the dominant ink color matches the measured gray.

Run on the asset band, the matching 150dpi render crop (--scale 2), and the
original-frame crop (ground truth). A judge PASS never waives it.
references/equations.md ("Straight-bar delimiter law") owns the law.

usage:
  python3 check_bars.py <image> [image ...]
      --expect "x0:x1=y0:y1[=RRGGBB],..."   one term per delimiter window
                                            (columns x0..x1, rows y0..y1;
                                            expected hex color optional)
      [--lum-threshold T]   ink threshold for opaque images (default 200)
      [--alpha-threshold A] ink threshold for RGBA (default 64)
      [--scale S]           image scale vs frame px (150dpi render = 2, 600dpi
                            asset = 6.25); scales tolerances (default 1)
      [--col-tol C]         straightness tolerance in frame px (default 1)
      [--span-tol R]        span tolerance in frame px (default 2)
      [--color-tol K]       per-channel color tolerance (default 16; the deck
                            grays 909090 / A6A6A6 / 6E6E6E sit 22-56 apart)
      [--min-frac F]        fraction of span rows that must carry ink (default 0.9)

exit 0 = every window holds one straight bar of the expected span/color;
exit 1 = any failed window (fail loud — rebuild; reason printed per window).
"""
import sys
import numpy as np
from PIL import Image


def load_ink(path, lum_t, alpha_t):
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    if arr[:, :, 3].min() < 255:  # transparency present -> alpha is the ink map
        return arr[:, :, 3] > alpha_t, arr[:, :, :3].astype(int)
    lum = arr[:, :, :3].mean(axis=2)
    return lum < lum_t, arr[:, :, :3].astype(int)


def check_window(ink, rgb, x0, x1, y0, y1, color, scale, col_tol, span_tol,
                 color_tol, min_frac):
    S = scale
    ys = slice(int(y0 * S), int(np.ceil(y1 * S)))
    xs = slice(int(x0 * S), int(np.ceil(x1 * S)))
    win = ink[ys, xs]
    if not win.any():
        return "no ink in window"
    rows = np.where(win.any(axis=1))[0]
    frac = len(rows) / max(1, win.shape[0])
    if frac < min_frac:
        return f"ink on only {frac:.0%} of span rows (min {min_frac:.0%}) - not a bar"
    cols = np.where(win.any(axis=0))[0]
    if (cols.max() - cols.min() + 1) > (3 * S + 1):
        return f"ink too wide ({cols.max() - cols.min() + 1}px at scale {S}) - not a hairline bar"
    counts = win.sum(axis=0)
    modal = int(np.median(np.where(counts > 0)[0]))
    drift = sum(
        1 for r in rows if abs(win[r].nonzero()[0].mean() - modal) > col_tol * S
    )
    if drift:
        return f"{drift} span rows drift >{col_tol}px off the modal column - CURVED, not a bar"
    top = y0 + rows.min() / S
    bot = y0 + rows.max() / S
    if abs(top - y0) > span_tol or abs(bot - y1) > span_tol:
        return f"span {top:.1f}..{bot:.1f} misses measured {y0}..{y1} (tol {span_tol}px)"
    if color:
        px = rgb[ys, xs][win]
        dom = np.median(px, axis=0)
        if np.abs(dom - np.array(color)).max() > color_tol:
            return f"dominant ink RGB{tuple(int(v) for v in dom)} != expected {color}"
    return None


def parse_args(argv):
    imgs, opts, expect = [], {}, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--expect":
            expect = argv[i + 1]
            i += 2
        elif a.startswith("--"):
            opts[a[2:].replace("-", "_")] = argv[i + 1]
            i += 2
        else:
            imgs.append(a)
            i += 1
    return imgs, opts, expect


def parse_windows(expect):
    wins = []
    for term in expect.split(","):
        parts = term.split("=")
        x0, x1 = (float(v) for v in parts[0].split(":"))
        y0, y1 = (float(v) for v in parts[1].split(":"))
        col = parts[2].strip() if len(parts) > 2 else None
        color = tuple(int(col[k:k + 2], 16) for k in (0, 2, 4)) if col else None
        wins.append((x0, x1, y0, y1, color))
    return wins


def main():
    imgs, opts, expect = parse_args(sys.argv[1:])
    if not imgs or not expect:
        sys.exit(__doc__)
    wins = parse_windows(expect)
    failures = 0
    for path in imgs:
        ink, rgb = load_ink(path, float(opts.get("lum_threshold", 200)),
                            float(opts.get("alpha_threshold", 64)))
        for wi, (x0, x1, y0, y1, color) in enumerate(wins):
            why = check_window(
                ink, rgb, x0, x1, y0, y1, color,
                float(opts.get("scale", 1)), float(opts.get("col_tol", 1)),
                float(opts.get("span_tol", 2)), float(opts.get("color_tol", 16)),
                float(opts.get("min_frac", 0.9)),
            )
            tag = f"{path} window{wi} x{x0}:{x1} y{y0}:{y1}" + (
                f" #{'%02X%02X%02X' % color}" if color else "")
            if why:
                failures += 1
                print(f"FAIL {tag}: {why}")
            else:
                print(f"ok   {tag}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
