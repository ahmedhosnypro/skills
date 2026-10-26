# Building — pptxgenjs build, render, closed-loop checks

## Build script

`recreated_pptx/build/slide_NNN.js` using pptxgenjs. Run with:
`NODE_PATH=$(npm root -g) node build/slide_NNN.js` from the project root
(fallback for non-global installs: run from a directory where
`require("pptxgenjs")` resolves, e.g. the project's node_modules).

- `pres.layout = "LAYOUT_WIDE"` → 13.33 × 7.5 in. Originals at 960×540 px mean
  **1px = 1pt** — every measured original coordinate converts directly.
- Read the spec JSON fully first; honor `verbatim_text`, `layout`,
  `visual_elements`, `colors`, `typography_notes`, `recreation_brief`, and
  `validation.fixes`.
- **Spec text vs the original frame: the frame wins.** PIL-verify every
  spec-claimed visual element against the actual pixels before drawing it —
  specs describe elements the original never shows (an "annotation dot", axis
  titles) and omit ones it does (per-letter colored chip labels). A register's
  or spec's measured parameters are a guide, not ground truth: re-derive each
  item from the frame before executing it, and document frame-vs-spec
  deviations in the build header.
- Set `fontFace` explicitly on every text element (Arial unless the spec says
  otherwise); `margin: 0` on text boxes that must align with shapes.
- Bullets: pptxgenjs HAS native bullets (per-paragraph `bullet` option +
  `indent`) — glyph codes, indent law, and factory law in
  `references/pptx-engine.md`. Manual `"• "` prefixes remain the fallback
  for pinned-pitch geometry (they keep line pitch pixel-stable).

## pptxgenjs pitfalls (each caused a real bug)

Two more silent-corruption classes — rich-text `<a:pPr>` duplication from
unterminated runs, and option-object mutation by pptxgenjs internals — live in
`references/pptx-engine.md`.

- **Hex colors never carry `#` in pptxgenjs** — `#C00000` corrupts the pptx XML
  (LibreOffice can't open it). No 8-char hex either; use the `transparency`
  property. (Inverse rule for matplotlib/mathtext renderers: they REQUIRE `#` —
  see equations.md. Two parsers, two rules; check which parser eats the string.)
- **Empty-string text runs drop their options** (`{text:"", options:{fontSize:10}}`
  produced 20pt spacer lines — the XML got bare `endParaRPr`). A blank line is a
  single-SPACE run `{" "}` with explicit options + pinned `lineSpacing`.
- **Rotated shapes are declared in their UNROTATED frame**: rotate 90/270 spins
  the unrotated shape about its center and swaps the visual bbox — declare
  `w:px(hV), h:px(wV)` and translate `x/y` so the unrotated center lands on the
  visual center (wedge heads). Also NEVER combine preset shapes with `rotate:90`
  when LibreOffice renders the deliverable: LO swaps the preset's bbox axes and
  lands the ink elsewhere entirely (a stretched brace became a displaced
  vertical bar). Draw the rotated geometry directly as an upright shape.
- **Negative-height lines render a phantom duplicated segment** one pitch above
  the intended box (LO honors the box, duplicates the stroke) — use positive h +
  `flipV` (the `drawXmarks45` pattern). A run far taller than the frame's mark
  is the artifact signature.
- **`fill:{type:'none'}` on a custGeom emits EMPTY fill XML** → the shape
  inherits the theme fill and renders as a solid blob. Omit the fill option
  entirely to get `<a:noFill/>` (stroke-only bezier — pattern
  curved-arrows-custgeom).
- **`line.endArrowType:'triangle'` heads are size-locked to line width and tilt
  with the path tangent** — they can't match a measured head. Draw explicit
  triangle shapes at the measured bbox (flipV as needed).
- **Never use the ARC preset for thin curved strokes under LibreOffice** — LO
  renders it as two parallel strokes with merged caps (double-stroke blobs),
  visible at zoom, and partial sweeps cover only the middle ~half of the bbox.
  Curved delimiters = single quadratic-Bézier centerline → 600dpi transparent
  PNG at exact size (pattern delimiters-bezier-png); bank a zoomed-crop
  certificate of the delimiter region (full-slide judges + PIL bbox cannot see
  double strokes). A large text-glyph paren is NOT an alternative (measured far
  too fat). SCOPE: curved forms are for delimiters whose ORIGINAL genuinely
  curves — matrix/vector paren pairs are STRAIGHT BARS (equations.md
  straight-bar law; pattern delimiters-straight-bars), never curves.
- **`addImage` at EXACT size** (`w = px/600` in for 600-dpi assets) — rescaling
  blurs glyphs. PNG only; LO rasterizes SVG unpredictably.

## Text laws

- **Wrap budget**: text wraps at BOX width, not ink width — size every box ~20%
  wider than the longest line's glyph advance (Arial ≈ 0.556em/digit), or a
  wrapped line will silently spill outside delimiters/frames. Extend PIL
  measurement windows below and around the expected band to catch wrap
  spillover; assert no-ink-below on every two-line stacked value.
- **lineSpacing is mandatory on every multi-line box** (LO auto pitch differs
  from PowerPoint's — LO checks under-predict PowerPoint overflow). The pin
  VALUE has two variants: **defect-fix pin** = measure the ORIGINAL's band
  pitch and pin that (fidelity re-judges); **compliance pin** = measure the
  current LO render's pitch and pin exactly that (a pixel-identical no-op that
  inherits certification — prove with n=0 pixel diff + pitch assertion).
  Single-line boxes: pin nothing, but assert one-band-per-element.
- **Close text-ink-width residuals with `charSpacing`, never font size.** Size
  bumps to fix width break cap-height/baseline metrics. Per line:
  charSpacing_pt = (residual/2)/gap_count. LO honors pptxgenjs charSpacing
  (measured +0.77pt/char).

## Tables

- **Budget table frames from LibreOffice's rendered row floor**, not nominal
  rowH: LO renders single-line 8pt rows at ~0.153in regardless of the requested
  height (a 36-row table came out ~13px over budget). Measure the rendered
  gridline extent, then size/move the frame; assert gridline count + per-side
  clearance.
- **Dataset tables read the ONE canonical CSV live** and are proven by cell
  assertion, never a full-slide judge's transcription (pattern
  table-from-dataset + `assert_cells.py` extracts the table from the pptx XML
  and asserts every cell). Derive ambiguous displayed-row sets from forensics
  (PIL band counts + class-color composition + the CSV's class boundaries), and
  settle disputes with a zoomed same-scale crop-pair comparison. A hardcoded
  transcription that shifts rows passes judges — the canonical-file assertion
  is what catches it (a 7-row shift on a real deck).

## Delimiters, strokes, and drawn shapes

- **Enclosing delimiters (parens/brackets/boxes) are SHAPE-like elements with
  their own measured geometry** — never synthesize them from per-line text
  glyphs. Measure their full band in the original and draw them to span every
  enclosed row: half-turn arcs (`angleRange [90,270]/[270,450]`, tiny rx) per
  side; smooth curved delimiters via the Bézier-PNG pattern above — UNLESS the
  pair encloses matrices/vectors/digit stacks, which are straight bars
  (equations.md straight-bar law). Two
  full-slide judges have PASSED delimiter defects — delimiter geometry lives
  below judge resolution; verify with x3+ zoomed crop comparisons before
  judging.
- **Fat filled arrowheads/markers (fill >70% of bbox) need a composite of two
  overlapping triangles** — a single thin triangle leaves hollow flanks
  (25-32px ink vs the original's 53-68). Verify with an ink-pixel count inside
  the measured bbox.
- **Diagnose stroke wobble at 600dpi, never 150dpi** — centerline maxdev is
  AA-dominated at 150dpi (indistinguishable before/after); count edge
  signflips@1px on a 600dpi trace. When a raster-curve asset needs
  smoothness-only repair, re-render the asset's own knot data as a native
  custGeom Bézier (Catmull-Rom → cubic B1=P1+(P2-P0)/6, B2=P2-(P3-P1)/6) —
  never re-trace, never patch in the parent (child-local erase + repaint at
  parent geometry for inherited artifacts).
- **Closed-loop stroke/curve comparison uses point-to-ink distance** (e.g.
  scipy cKDTree from original centerline points to render ink), never per-row
  coordinate diffs — grid offsets amplify to phantom error on near-horizontal
  strokes.

## Z-order, containment, and masking

- **Per-element bbox checks cannot catch z-order masking** — when one element
  is drawn over another's region (image under caption, panel under box, later
  chain over early pills), add a **GAP-BAND assertion**: a strip between
  adjacent elements that must be pure background (0 non-bg px). A later-drawn
  caption box can silently hide a frame crossing.
- **Swapping native elements for measured images re-opens containment of every
  surrounding frame**, not just the one touched — re-check EVERY adjacent
  element for collisions and reproduce the ORIGINAL's own geometry for the
  neighbors (original geometry wins over inherited composition positions).
- **Cover-then-redraw covers must span the OLD ink's full measured extent** — a
  cover sized to the new element leaves the old element's extremities (triangle
  heads span y±2.5 even on a 0.5pt line). x-trim short of neighboring borders.
- **Judge occlusion findings need BOTH fixes**: narrow the offender to the
  frame-measured footprint AND move the flagged elements' draw calls to after
  the covering cascade.
- **LibreOffice containment is not PowerPoint containment**: PowerPoint does
  not clip overflowing text boxes and font-fallback line boxes run ~1.2-1.4em,
  so keep ≥ ~0.5in clearance at the content-dense edge of any inner frame. The
  canonical owner-approved fix: raise the frame's top, increase its height,
  shift contained content up rigidly by the same amount (bottom edge is
  bounded by the house frame stroke — untouchable). Owner-ordered deviations
  from the original are legitimate; judges accept them.
- **Highlight boxes**: ≥ ~4.5pt clearance from the longest line's last glyph to
  the fill edge (under 2pt a tall glyph visually touches the border); widen
  right-only to keep other regions pixel-identical (pattern highlight-box).

## Asset laws

- **Every frame decides its own assets — never cross-seat a sibling's** (a
  sibling's swoosh/ribbon cut through certified content when reused at another
  seat). Re-trace per frame and IoU-verify in slide space (mapping-corrected).
- **Baked-crop photos with capture artifacts** (screen cursor over a digit):
  pattern cursor-inpaint-restore — measure the artifact's full outline, fill
  iteratively with content-protecting sources, restore damaged glyphs by twin
  alpha-blend, prove numerically + zoomed crop.
- A shared certified equation/graph asset keeps its provenance values across
  slides: prove identity by md5 + embed-box geometry, never by re-rendering
  (equations.md).

## Rendering infra

```
soffice --headless --convert-to pdf --outdir <qa_dir> <pptx>   # private profile!
pdftoppm -png -r 150 <pdf> <qa_dir>/render_K
```

- **Private LibreOffice profile** (`-env:UserInstallation=file:///...`) — shared
  profiles cause inconsistent renders and blocked locks.
- 150dpi render of a 960×540-original slide → scale ×2000/960 when comparing to
  original-frame measurements. Compute effective scale per axis when the
  frame→slide mapping is anisotropic (judging.md crop law).
- **LO failures can be path- AND time-dependent — re-verify the route, don't
  assume yesterday's command still works.** Known host failure mode: LO
  silently replaces all embedded raster images with broken-image placeholder
  text on direct PPTX→PNG export and fails PPTX→PDF from deep paths. Validated
  workaround: copy the pptx to a short home path (`/home/<user>/lo_pdf_test`),
  soffice→PDF there, pdftoppm, copy back. **Treat "missing images" judge
  findings on an unchanged build as infra first** — grep renders for the
  placeholder pattern BEFORE trusting any pixel metric (early ink measurements
  have counted placeholder glyphs).
- The vision gate and LO sessions need `TMPDIR` redirected to project scratch —
  a broken/temporary-quota host /tmp kills them silently (operations.md).

## House chrome (per deck family)

ONE outer template per **deck family**, measured from the family's reference
slide — never assumed from another family:

- **Starting a new family/course**: PIL-measure the reference slide's chrome
  FIRST (canvas, panel, frame inset, badge position/size/colors, title box),
  codify it in a family-level instructions file + shared-patterns dir (runnable
  `house_chrome.js` + `house_chrome_check.py` closed-loop checker), and only
  then dispatch builders. Per-deck instruction files reference it and cannot
  relax it.
- **Example instance A** (illustrative — measure your own family; never copy
  blindly): background `E8E8E8`; outer frame `x:0.15, y:0.15, w:13.03, h:7.2`,
  line `C00000` 1.5pt, no fill; badge yellow circle `x:12.48, y:0.30, w:0.5,
  h:0.5` (fill+line `FFF9C4`), bold 18pt centered numeral `333333`; title box
  `y:0.28, x:0.6, w:12.13` centered. An intentionally empty title
  (`[No title ...]`) is conformant.
- **Example instance B** (a different measured family): white `FFFFFF` canvas;
  gray `E9E9E7` panel inset left/right/top, bottom at slide edge; red `C00000`
  border; yellow `FDFD96` badge with a purple `6A5ACD` ~2pt ring; bold `333333`
  numeral — and different geometry again. The point: families differ
  materially; measure per family.
- **Badge numeral = the number printed on the ORIGINAL slide image** — in a
  curated deck the file is named by that printed number, so the badge reads
  exactly `N` (unpadded). A badge not matching the original's print is WRONG
  even if judges never complained. Judges misread small numerals — that
  finding is overridden, noted in close-out (occluded digits: judging.md
  sibling-IoU law).
- **Chrome-checker false positives**: when `house_chrome_check.py` fails ONLY
  the badge while panel/border checks pass, check whether measured original
  content intrudes the badge window (e.g. a tan bar matching the yellow mask)
  before "fixing" the build — verify the intrusion exists in the original
  frame.

## Copy-then-modify discipline

- Never edit a certified build in place: `cp build/slide_NNN.js
  build/slide_NNN_<variant>.js` and modify only the copy.
- Before ANY change, bank the current state: `cp build/slide_NNN.js
  qa/slideNNN/build_pre_<change>.js`. Every attempt keeps `build_attempt_K.js`,
  `render_K.png`, `probe_K.txt`, `judge_prompt_K.txt`, `judge_attempt_K.txt`.
- Never delete banked evidence, including old-numbered builds from previous
  curations.

## Closed-loop checker discipline

The closed loop (measure original → build → render → PIL-compare → iterate) is
mandatory before judging; these laws keep the CHECKER honest:

- **A checker's FAIL is a claim, not a verdict** — verify the checker's units
  and windows before believing it. The four measured trap classes: (1) windows
  that clip the element's true ink extent (manufactured phantom errors); (2)
  y-windows that clip ascenders/descenders; (3) scans that match TEXT rows
  before reaching the feature (underlines: scan only baseline+1..+6pt); (4)
  wide "identical" windows that catch box borders, neighbors' ascenders, and
  the pen cursor.
- **Identical windows on BOTH images**: run the SAME predicates/windows on the
  original frame to self-derive targets — JPEG-antialias bleed cancels on both
  sides; hardcoded targets drift.
- **Probe boxes come from the draw code's CURRENT coordinates**, never an
  earlier geometry note — a stale probe lands in empty space (false FAIL) or
  "passes" via incidental line-crossing. Re-derive every probe box when
  inheriting a dead worker's verify scripts.
- **Mask discipline**: measure the BACKGROUND's own redness/blueness and set ink
  thresholds ≥15 above it (peach panels pass naive redness scans); non-red
  faint ink needs a min-channel scan — "no ink found" by one mask is not
  absence until a second mask has run; masks that merge two elements tighten
  on the SATURATION axis (G channel), not hue; strict masks on JPEG originals
  systematically drop mid-tone strokes (complement with edge-gradient/dilation
  or a sensitive `|px-255|.max > 25` mask); dense-column statistics need
  per-run segmentation with a min-size glyph filter or unrelated content
  poisons the measurement.
- **Pixel-diff comparisons at non-integer frame-px shifts are AA noise** for
  sub-2px strokes — census ink per region/class (colhists, connected
  components) or shift crops to a common integer grid.
- **Feature-presence checks walk sub-pixel along the expected geometry**
  (0.05px), not an integer lattice that steps over 2-3px features; matplotlib
  dash specs scale by line width (divide the target by lw and count dashes in
  the render).
- **Fix the checker, then re-run, before treating a FAIL as a defect** —
  otherwise you "fix" a correct slide against a broken assertion.
- PIL self-checks corroborate; they NEVER substitute for the visual judge
  (judging.md).
