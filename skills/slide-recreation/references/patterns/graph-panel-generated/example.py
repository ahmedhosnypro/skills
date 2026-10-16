#!/usr/bin/env python3
"""Pattern: graph-panel-generated.

Advanced graphs (scatters, PCA projections, decision regions — anything native
chart shapes can only approximate) are EMBEDDED from a properly generated image:
the topic-correct library running the SAME algorithm on the REAL data.

This demo: a 2-component PCA projection of a labeled dataset. Adapt the
library/function/algorithm/data PER SLIDE (KNN -> sklearn.neighbors meshgrid;
polyfit curves -> numpy.polyfit at the original's degrees; etc.).

Laws:
 - MEASURE, DON'T TRUST THE SPEC: match the original's measured colors, marker
   sizes, axis ranges, region geometry — the spec is a lossy description.
 - MARKER-EDGE INFLATION: matplotlib "o" markers draw the markeredge stroke
   (default lw 1.5pt) HALF OUTSIDE the nominal radius. When sizing dots from
   absolute measured radii, pass markeredgewidth=0. (Dots calibrated THROUGH
   rendered pixels already include the edge — never mix calibration styles.)
 - GLOSSY BALL = 3 STACKED DISCS: a top-lit shaded dot = base disc (dark rim,
   full radius) + mid disc (brighter, smaller, offset up) + core disc (brightest,
   smallest, slight offset). Calibrate radii from multi-threshold angular-
   coverage walks; the faded halo beyond is blur, not paint.
 - PATCH DASH SPECS SCALE BY LINE WIDTH: Circle(..., lw=L, linestyle=(0,(a,b)))
   renders EFFECTIVE (a*L, b*L) — divide the spec by lw to get true on/off pt.
   ALWAYS count the dashes in the rendered PNG, never trust the spec.
 - BAKE region borders INTO the image (overlay borders misalign).
 - Verify with PIL masks before spending a vision call; then a graph-region
   vision comparison; then the full-slide judge — all three legs required.

Run:  python3 example.py   -> demo_graph.png
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA

# ---- parameters (from the original's measured region) ------------------------
REGION_PX = (70, 116, 885, 522)     # x0,y0,x1,y1 in the 960x540 frame (1px=1pt)
CLASS_COLORS = {0: "#FF0000", 1: "#0000FF", 2: "#2E8B22"}   # measured, not guessed
MARKER_PT = 7.5                    # measured solid dot radius -> markersize ~d pt
BG = "#FFFFFF"

# ---- generate (same algorithm on the real data) -------------------------------
X = load_iris().data
y = load_iris().target
Z = PCA(n_components=2).fit_transform(X)

w = REGION_PX[2] - REGION_PX[0]
h = REGION_PX[3] - REGION_PX[1]
fig = plt.figure(figsize=(w / 72, h / 72), dpi=72)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor(BG)
for cls, color in CLASS_COLORS.items():
    ax.scatter(Z[y == cls, 0], Z[y == cls, 1], s=MARKER_PT ** 2, c=color,
               linewidths=0)   # LAW: no marker-edge inflation (scatter edge = linewidths;
                               #  plot()-style markers use markeredgewidth=0)
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():   # LAW: bake the region border into the image
    spine.set_visible(True)
    spine.set_color("#AA0000")
    spine.set_linewidth(1.5)
fig.savefig("demo_graph.png", dpi=72, facecolor=BG)
print("wrote demo_graph.png — embed with addImage at the measured region, "
      "then closed-loop PIL-align before any vision call")
