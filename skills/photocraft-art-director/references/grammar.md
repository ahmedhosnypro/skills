# grammar.md — composition grammar for PhotoCraft artwork

The charter's grammar section answers one question per element: *what
mark language draws this subject so it reads as itself?* This file
holds the fit table, the register rules, the focal-hierarchy law, the
depth ladder, the layout law, and the repetition law. Each rule ends in
a probe or a named defect class (see `failure-classes.md`).

## 1. Subject → grammar fit table

Pick the row that matches the element's subject class. "Mark language"
is what the generator must produce; "register warning" is what breaks
the piece if ignored; "probe" is the cheapest acceptance check.

| Subject class | Mark language | Register warning | Typical probe |
|---|---|---|---|
| Water, waves | Curve-based silhouettes: asymmetric faces, swell on crests, swallowed tops, occasional double peaks and below-baseline notches; mirror-bright water may use exact coordinate reflection of the source | Straight-segment zigzag knots read as mountain ridgelines / cut paper in the first audit; no pitch jitter or anchor insert cures the class | Reflection knots mirror source knots (y → 2·horizon − y); crest-spacing std above its floor (no fixed pitch) |
| Clouds, foliage, fire | Curve grammars; mass distribution varies per instance; edges soft or broken, never polygon-faceted | Polygon silhouettes read as paper cutouts | Region-edge curvature: no long straight segments in the silhouette |
| Terrain ridges, dunes, mountains | Hand-authored knot tables with varied pitch and mass, jittered knot positions, horizon gaps between bands; low-frequency sine acceptable for gentle ground lines | Uniform-pitch procedural zigzag reads as clip-art / sawtooth; two bands sharing one pitch frequency read as a picket fence or zebra stripes | Crest-to-crest distance variance above floor; no two bands share the same dominant pitch |
| Stars, discrete points | Individual dabs in 2–4 size classes, seeded RNG placement, an exclusion halo around the brightest point | Noise grain reads as "grain masquerading as stars" — noise is ambience, not stars | Pixels-above-threshold count per size class; brightest star's halo respected |
| Aurora, ribbons, curtains | Striated ribbons: 2–3 bezier arcs, each with parallel offset striations, opacity rolling off from the center line | Amorphous soft blobs read as fog/clouds, not aurora; structure (striae) is the subject | Line profiles across the band show ≥3 luminance striations |
| Dust, grain, ambience | Procedural scatter: small hard dabs, seeded, low opacity, blurred | Scatter is for texture only — never primary forms; a scatter-built hero silhouette reads as confetti | Region mean/stdev delta vs empty sky; no visible stamp grid |
| Dark occluders on dark fields | One continuous varying stroke, tapered width, sin-peaked opacity, soft-but-not-vanished hardness | A machine-straight hard bar dominates the frame; a too-faint pass is invisible — both fail the same budget | Lane probe ≥ local background + declared value steps; hierarchy ratio vs anchor |

**The naming law.** Name every generator after the subject it
paints. A builder named for the wrong subject (`mountains()` reused
for storm water) plants a grammar-class defect in version 1 that
survives every cosmetic fix — the audit reads the *named* subject back
out of the render.

## 2. Register coherence — one mark family per piece

**One register per piece.** Two registers fighting reads as noise;
three reads as a collage. Declare the medium in the charter and let it
forbid its opposites:

| Medium declaration | Implies | Forbids |
|---|---|---|
| Brush-painted register | Visible stroke marks, hand-drifted geometry (±3px knot drift), textured fills | Machine-straight vector edges in primary forms; pure smooth gradients as the only surface |
| Soft-glow airbrush register | Blurred soft strokes, washes, glow beds by design | Bristle texture; crisp machine edges; hard-crescent dashes |
| Flat-graphic / hard-geometry register | Crisp vector silhouettes, flat fills, deliberate edges | Washes inside polygons; painterly bleed across edges |
| Photo-realist register | Graded tones, lens physics (depth blur, bloom) | Naked procedural periodicity anywhere |

**Register conflicts auditors actually find:**

- A crisp vector focal in a wash field reads as a pasted-on overlay —
  and lands on the one element you can least afford to lose. Build the
  focal from the piece's own mark language (a stroke fan from the
  exact light point), never a blurred solid.
- Painterly washes inside hard-faceted polygons read as "three
  registers fighting" — silhouette curvature must match the fill's
  register.
- Airbrushed glow laid over painterly strokes reads as an imported
  overlay. Match the dialect or declare the whole piece airbrush.

**The medium is the audit contract.** Audits score the piece against
the declared register. Freezing the declaration before round one and
never silently rewriting it later is what keeps identical pixels from
being a defect in one version and a strength in the next. If the
declaration must change, log a scope change in the charter and restate
the audit contract — see `spec drift` in `failure-classes.md`.

## 3. Focal hierarchy — exactly one first-glance anchor

- **One anchor.** The charter names the element that must win the eye
  first, and the runner-up. Everything else supports.
- **Warm-in-cold is the cheapest reliable device**: one warm element in
  a cold scene, at most one accent color from one temperature family,
  used once. It works from version 1 and survives every later edit —
  when it is built from the piece's own marks.
- **Hierarchy-ratio budget.** Give the anchor a numeric margin over
  its nearest competitor: peak luminance, saturated-pixel count, or
  contrast delta, probed at fixed coordinates. "The core must win the
  eye" without a number is hostage to per-audit taste; "anchor probe ≥
  competitor probe × ratio" is checkable.
- **Focal inversion is a named defect**: a secondary luminous element
  (a moon, a dust lane, a teal glow) out-contrasting the declared
  anchor. Check the hierarchy ratio before the first audit, not after.
- **Sub-tuning the anchor's competitor is usually the fix**: dim, split,
  or de-fang the competitor (two gapped segments framing the core
  instead of one bisecting bar), rather than pushing the anchor brighter.

## 4. Depth — a value ladder plus graded mark dialect

Depth is sold by *value structure plus mark grading*, not by counting
layers or bands:

- **Value ladder**: each depth band gets its own value stop, derived
  from the palette rules (`palette-light.md`), near dark → far light
  (or the scene's declared direction). A ladder that collapses (two
  bands sharing one value) reads as one flat band.
- **Dialect grading**: within one mark family, grade size, opacity,
  blur, and dropout by distance (e.g. rim marks shrink, fade, soften,
  and skip more often with distance). Grading *values only* leaves
  equal dashes reading as a fringe; grading *geometry only* leaves the
  far bands mismatched.
- **Mark-family continuity — attenuate, never zero**: a mark family
  stays present within and across bands. If a light accent (rim,
  glint) drops out on some members of the same band at the same angle,
  that is the `within-band mark dropout` defect; restore the family
  with a faint uniform echo rather than re-carving.
- **Edge softness grades with distance**: feather far bands
  (rasterize + blur in slot), keep near bands crisp. A hard seam at
  the far/mid boundary reads as a pasted layer.
- **Depth-attenuated reflections**: water reflections fade with
  distance from the horizon via transparency ramps on a shading pass,
  so they dissolve instead of stopping at one shared line.

## 5. Layout — horizon, weak thirds, overscan

- **Horizon placement is a charter decision**, declared as a ratio and
  probed at a fixed x: an off-center split reads as composition; a
  dead-center split reads as a test pattern. State the ratio in the
  charter so audits can check layout against it.
- **Weak-third closure**: walk the frame's thirds at charter time and
  name one feature per region likely to read flat. Featureless sky or
  foreground vacuums get either a deliberate emptiness declaration or
  a named filler.
- **Close the frame cheaply at the end**: the last +1 comes from small
  named features (shore mounds, reeds, birds, stars, sparkle glints)
  placed exactly in the regions prior audits called flat.
- **Overscan all geometry and washes past the canvas edge** so
  nothing terminates visibly mid-canvas (extend strokes and paths
  beyond both edges; close silhouette bases past the corners). A wash
  cut at the border produces a hard edge-step defect at the frame.
- **Sun/lights placed off-center** (a declared fraction of the width)
  so the light system has somewhere to point; record the position —
  every rim, glint, and bleed traces back to it.

## 6. Repetition law — periodicity is the noise signature

Periodicity is what makes procedural art read as procedural. Equal
pitch, equal dash length, and uniform stamps are all the same defect
seen on different elements:

- **Kill repetition at the generator, never at the surface.** Vary
  pitch per segment (segment length a range like 0.55–1.7× the mean,
  not a constant), vary mass distribution, jitter knot positions, and
  add swell/notch/dropout events with seeded randomness. Three
  cosmetic rounds of blur or anchor-insertion against periodicity fix
  nothing; one generator reseed does.
- **Check pitch variance at generation time**: print the crest-gap
  list, compute the standard deviation, and compare against the
  charter's floor. Exact-integer gaps (every crest the same distance)
  are the fingerprint of the defect.
- **Chunked strokes leave bead seams**: painting a curve as constant-
  spacing sub-strokes produces stamp-periodicity the audit catches
  instantly. Vary spacing and size per chunk, or paint one
  overlapping continuous stroke.
- **Scatter is for texture; knots are for heroes.** Procedural scatter
  belongs to ambience layers (grain, mist pockets, mid-band texture).
  Hero silhouettes are hand-authored knot tables — seeded uniform-pitch
  generators reliably read as clip-art on the primary form.
- **Uniform marks read as fringe**: rim dashes at one size/brightness
  read as an applied sticker fringe; jitter size, opacity, and skip
  threshold together, and taper runs to nothing at both ends.

## 7. Charter checklist (grammar section)

1. One sentence of subject + register (medium declaration, frozen).
2. Per major element: subject class → mark language → generator or
   hand-knot source, named for the subject.
3. Hierarchy: anchor, runner-up, hierarchy-ratio budget.
4. Depth ladder: per-band value stops + dialect grading table.
5. Layout: horizon ratio, weak-third plan with named fillers.
6. Repetition floors: pitch-variance floor per repeated element.

Every line above becomes a probe in the acceptance budgets
(`acceptance.md`) — if it cannot be probed, it is not in the charter.
