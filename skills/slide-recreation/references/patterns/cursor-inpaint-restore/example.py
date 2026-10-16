#!/usr/bin/env python3
"""Pattern: cursor-inpaint-restore — remove a screen-recording cursor (or similar
small capture artifact) that is BAKED INTO a frame-cropped photo, then restore any
content glyph the cursor damaged by alpha-blending a clean twin from the same image.

When to use: the deck's originals are lecture screencaps; cursors overlap content.
The spec orders cursors excluded (ground rule (c): omission is CORRECT), but the
photo can only be sourced by cropping the frame — so the artifact must be inpainted
out of the CROP, never left baked in.

Laws (earned on a real certified-deck case; vision-certified):
1. MEASURE the artifact first (PIL near-black non-red class map over the region) —
   never guess its extent. The worked case's cursor outline reached x338..384 while the
   obvious blob suggested x346..380; a too-tight erase window leaves dark outline
   segments that then propagate into the fill.
2. ERASE only artifact-colored pixels inside the measured window (+2px halo):
   near-black (lum<135) AND not content-red. Killing a broad lum band destroys the
   photo's own mid-dark content and invites red bleed from neighboring glyphs.
3. FILL ITERATIVELY inward (radius-2 median of already-filled neighbors), repeated
   until every erased px has a value — a single radius-2 pass leaves THICK artifact
   interiors unfilled (no known neighbor within radius). Fill sources exclude red
   px AND near-black px (a neighboring glyph's dark anti-aliasing halo otherwise
   propagates a dark streak through the filled region).
4. SMOOTH the fill: one 7x7 non-red median over every erased px votes out residual
   dark-bleed; verify residual lum<100 non-red count ~0 inside the window.
5. RESTORE damaged content glyphs by ALPHA-BLENDING a clean twin from the same
   image (same font/size row), alpha = ink-ness (e.g. clip((R-G)/150)) so the
   glyph's anti-aliasing transfers without its background. Verify numerically:
   restored glyph red-px count ≈ twin's, untouched neighbors' counts unchanged,
   ghost-zone counts = original's.
6. Re-verify with a ZOOMED CROP comparison through the vision gate (the judge must
   confirm the restored glyph against its twin); cursor absence is settled by
   ground rule (c), the restored glyph is not.

Run: python3 example.py <frame.jpg>
(The crop/window constants below are the validated worked case, kept so the
numbers in the comments stay meaningful; RE-MEASURE every constant for your own
frame per law 1. Prints verification numbers.)
"""
import sys
import numpy as np
from PIL import Image

SRC = sys.argv[1]  # the original frame carrying the baked-in artifact
OUT = "/tmp/pattern_cursor_inpaint_demo.png"  # demo output; real runs write build/assets/

a = np.asarray(Image.open(SRC).convert("RGB")).astype(float)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
red = (R > 130) & (G < 90) & (B < 90)

# ---- crop the photo that carries the baked artifact (x105..442, y284..454) ----
L, T = 105, 284
photo = a[T:455, L:443].copy()
ph, pw = photo.shape[:2]
pl = 0.299 * photo[..., 0] + 0.587 * photo[..., 1] + 0.114 * photo[..., 2]
pred = (photo[..., 0] > 130) & (photo[..., 1] < 90) & (photo[..., 2] < 90)

# ---- 1+2. erase mask: measured cursor window x336..388 y385..432 (+halo), lum<135, non-red ----
GX0, GX1, GY0, GY1 = 336, 388, 385, 432
lx0, lx1, ly0, ly1 = GX0 - L, GX1 - L, GY0 - T, GY1 - T
erase = np.zeros((ph, pw), bool)
erase[ly0:ly1 + 1, lx0:lx1 + 1] = (~pred[ly0:ly1 + 1, lx0:lx1 + 1]) & (pl[ly0:ly1 + 1, lx0:lx1 + 1] < 135)

# ---- 3. iterative inward fill (radius-2 median; sources: filled, non-red, not near-black) ----
filled = ~erase.copy()
fill = photo.copy()
for _ in range(80):
    todo = np.where(~filled)
    if len(todo[0]) == 0:
        break
    for y, x in zip(todo[0].tolist(), todo[1].tolist()):
        ys, xs = [], []
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                ny, nx = y + dy, x + dx
                if 0 <= ny < ph and 0 <= nx < pw and filled[ny, nx] and not pred[ny, nx] \
                        and fill[ny, nx].mean() >= 100:
                    ys.append(ny); xs.append(nx)
        if ys:
            fill[y, x] = np.median(fill[ys, xs], axis=0)
            filled[y, x] = True
photo = fill

# ---- 4. 7x7 non-red median smoothing over the erase mask ----
sm = photo.copy()
kys, kxs = np.where(erase)
for y, x in zip(kys.tolist(), kxs.tolist()):
    vals = [fill[y + dy, x + dx] for dy in range(-3, 4) for dx in range(-3, 4)
            if 0 <= y + dy < ph and 0 <= x + dx < pw and not pred[y + dy, x + dx]
            and fill[y + dy, x + dx].mean() >= 100]
    if vals:
        sm[y, x] = np.median(np.array(vals), axis=0)
photo = sm

# ---- 5. restore the damaged bottom-right '1' from the clean top-right '1' (dy=+91) ----
SY0, SX0, SY1, SX1 = 312 - T, 356 - L, 343 - T, 380 - L
DY = 91
src = photo[SY0:SY1 + 1, SX0:SX1 + 1]
alpha = np.clip((src[..., 0] - src[..., 1]) / 150.0, 0, 1)[..., None]
dyy = SY0 + DY
dest = photo[dyy:dyy + src.shape[0], SX0:SX1 + 1]
photo[dyy:dyy + src.shape[0], SX0:SX1 + 1] = dest * (1 - alpha) + src * alpha

# ---- verification (law 5): residual dark, glyph counts, ghost zones ----
cl = 0.299 * photo[..., 0] + 0.587 * photo[..., 1] + 0.114 * photo[..., 2]
crd = (photo[..., 0] > 130) & (photo[..., 1] < 90) & (photo[..., 2] < 90)
resid = int(((~crd[ly0:ly1 + 1, lx0:lx1 + 1]) & (cl[ly0:ly1 + 1, lx0:lx1 + 1] < 100)).sum())
g_new = int(crd[405 - T:432 - T, 357 - L:380 - L].sum())   # restored bottom '1'
g_ref = int(crd[314 - T:341 - T, 357 - L:380 - L].sum())   # clean top '1' (twin)
print(f"residual artifact px (expect ~0): {resid}")
print(f"restored glyph red px {g_new} vs twin {g_ref} (expect close)")
assert resid < 30 and abs(g_new - g_ref) < 40, "pattern verification FAILED"
Image.fromarray(photo.round().astype(np.uint8)).save(OUT)
print(f"OK -> {OUT}")
