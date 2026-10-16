# Graphs — AI-algorithm-generated chart images, single-version rule

Binding rules: slides whose originals contain advanced graphs (3-D scatters,
PCA projections, learned-model plots, decision regions — anything native
pptxgenjs shapes can only approximate) get a **properly GENERATED graph
image**:

- **Single version per slide**: the deliverable is ONE pptx per slide named
  `slide_NNN_recreated.pptx` — NO `_graphed`/`_omml` suffixes. A graph slide's
  own pptx HAS the generated graph embedded (the native-shapes approximation
  is replaced by the image in the same build; superseded builds live only in
  QA evidence dirs).
- Images are produced by the **correct Python library for the slide's topic**
  running the **same AI algorithm on real data** — not hand-drawn dot
  approximations:
  - PCA slide → `sklearn.decomposition.PCA` on the canonical dataset the
    original used (e.g. the standard iris data — `sklearn.datasets.load_iris`
    or a canonical CSV equivalent; never hardcode rows);
  - KNN decision regions → `sklearn.neighbors.KNeighborsClassifier(K=...)`
    fitted on measured training points, prediction over a meshgrid;
  - polynomial overfit/underfit curves → `numpy.polyfit` at the original's
    degrees on the measured training points.
- Library/function/algorithm/data are chosen **per slide**; web research is a
  best-effort aid, never a hard dependency: when the research tool is down and
  the plan is already ratified, proceed and let judges + PIL confirm.
- Tooling: a dedicated venv subproject for generation (pinned requirements) so
  the scientific stack stays reproducible.

## Workflow per slide

1. **Triage the original**: PIL-measure the graph region (frame, axes, palette,
   point positions). Reused vector art across slides is common in course decks —
   five sibling slides in one deck shared a single 26-point network scene;
   extract the canonical point list ONCE and reuse it across the family (drift
   ≤2px in practice).
2. **Generate** the image matched to the original's measured region/colors
   (960×540, 1px=1pt). Bank script + PNGs under the slide's QA dir.
3. **Closed-loop alignment** (same law as equations): PIL ink-edge match vs the
   original's measured placement within ~4px at 150dpi BEFORE any vision call.
4. **Graph vision leg**: comparison of the generated graph vs the original
   frame through the vision gate (default route, wide wall, scoped to the graph
   region ONLY — house chrome/badges/titles out of scope), ending "FINAL
   VERDICT: PASS or FAIL for 'faithful, usable graph match'". Fix loop per the
   judging law.
5. **Embed**: modify the slide's own build (`build/slide_NNN.js`) — native
   approximation → `addImage` at the measured region; house frame, badge, and
   ALL text unchanged; build `slide_NNN_recreated.pptx` (the single plain-named
   deliverable); render.
6. **Slide judge leg**: full judge comparison of the render vs the original
   with the mandatory ground-rules template. PASS from a winner body only.

## Extraction laws (measuring the original before generating)

- **Never trust a single color threshold for point extraction.** Strict masks
  systematically miss the DARKER cores of the same palette (7 found vs 31 true
  on a real slide) and mid-tone strokes washed out by JPEG compression (an
  entire axis invisible to a strict mask; washed strokes survive at loose
  thresholds — rescan with lum<225 for faint extents). Cross-check counts with
  a second, looser/darker mask per color + a one-shot vision probe for
  structure.
- **Absence of ink under strict masks is NOT absence of ink.** For any
  spec-mentioned thin/small element (leader lines, hairlines, arrowheads): one
  sensitive-mask dump (`|px-255|.max > 25`) + one gated high-zoom read (4-5x
  LANCZOS crop) before omitting it; the dense-region crop comparison
  arbitrates these regions.
- **Confirm the dataset/algorithm against the frame**: compare the original's
  axis tick ranges to the candidate algorithm's output on the candidate data
  (measured: unscaled-iris PCA tick ranges matched exactly) before generating.
- **When the original's plot contradicts its own labeled algorithm, reproduce
  the original.** This pipeline recreates the original's pixels — if no honest
  parameter configuration can reach the displayed geometry, prove the
  contradiction with a config sweep, reproduce the measured topology (fitted
  band model etc.), and document the deviation in the report + module
  docstring.
- **Cross-validate measured coordinates with multiple independent signals**
  before fitting anything: tick positions + geometric landmarks + LSQ
  residuals, and a sibling frame's readable markers when the scene repeats. A
  wrong calibration produces confident-looking but wrong curves.

## Generation laws (measured)

- **Verify the OUTPUT's per-class colors with PIL sampling after every
  generation pass** — color-guard heuristics in draw loops repaint data (a
  `min(rgb)>25` background guard flattened darker class dots flat cyan; two
  judges caught it before PIL). Mask explicitly by measured class palettes.
- **Bake region borders INTO the generated image** rather than drawing pptx
  shape borders on top — overlay misalignment is a defect class of its own.
- **Extend the canvas to the original's measured white body** (identical ink),
  not the plot bbox — a graph-sized canvas leaves gray margins that probes
  read as "panel clipping".
- **matplotlib marker EDGE stroke silently inflates every marker ~0.75pt in
  radius** — radial transects (45° color walks) on the render are the only
  sizing evidence trusted; a banked checker calibrated with the inflation
  baked in stays wrong.
- **Dash specs scale with line width** — matplotlib multiplies a patch's
  `(0,(on,off))` pattern by lw; divide the target by lw and count dashes in the
  render.
- **Feature-presence checks walk sub-pixel along the expected geometry**
  (0.05px), never an integer lattice — a lattice steps over 2-3px polygons
  and reports "missing" arrowheads that are present.

## Embed laws

- **After embedding a measured-correct graph, re-check EVERY surrounding
  element for collisions** (captions vs the graph's axis band) — resolve by
  matching the original's geometry, never by nudging the graph away from its
  measured position; document any caption move in the report.
- The embedded image may invalidate inherited caption/frame positions from the
  base native build — the original frame's own geometry wins (caption top =
  original measured px).
- Gap-band assertions around the embedded image are mandatory (building.md
  z-order law) — a later-drawn caption box can mask a frame crossing.

## Judge-leg notes

- House chrome and spec-inherited content are NOT fix triggers on the graph leg
  (judging.md inheritance law) — remedied by a clean re-judge carrying pixel
  ground truth in the context fields, never by editing the certified
  composition.
- A graph slide whose original graph is decorative may be skipped — record the
  skip decision explicitly rather than leaving it ambiguous.
- Keep superseded builds banked in the QA evidence dir (per-attempt
  provenance), never as parallel deliverables.
