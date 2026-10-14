# palette-light.md — palette derivation and light logic

Palette and light are one system: the source position fixes where
every luminous pool, glint, rim, and bleed may sit, and formulas fix
how related fields derive from the anchors. Derived structure is
correct by construction — audits can only attack surface language,
never structure (`grammar.md` Law 2).

## 1. Derivation recipes — derive, don't pick

Wherever a physical relation exists between two fields, compute the
dependent field from the anchor instead of hand-picking it.

| Relation | Recipe | Probe |
|---|---|---|
| Water from sky | Per stop: water = darken(sky stop, factor) + desaturate — e.g. darken(sky, 0.78), desat 0.18 | Sample the same x at sky and water: hue tracks, value darker by the declared factor |
| Mirror reflection | Reflection knots = exact coordinate mirror of source knots, y → 2·horizon − y | For each source knot, the reflection knot's y equals 2·horizon − y |
| Glint / light path on water | A segmented column at the light's x with a seeded wobble; segments grow with depth, opacity tapers | Path x == source x within tolerance; segment sizes follow the declared ramp |
| Rim light / crest rims | Per-crest strokes graded by azimuth distance from the source: atten = falloff(\|crest_x − source_x\|), with a floor (e.g. atten = max(floor, k/(1+((x−sx)/w)²))) | Rim value at the nearest crest ≥ floor + visibility steps; far rims fade smoothly |
| Depth attenuation | Far bands lighter or hazier per the value ladder; reflections fade with distance via a transparency ramp | Per-band value probe follows the ladder; no shared hard termination line |
| Shading / occlusion | Dark passes on dedicated normal-blend layers with graded opacities | Region mean below the unshaded baseline by the declared steps |

**Why derivation wins:** the relation holds by definition, so the
audit cannot attack it; re-verification is one probe, not a re-audit;
and a palette swap (time-of-day variant) is one constant change, not
a re-pick.

## 2. Light-source tracing — the pre-audit self-check

Before dispatching any audit, walk this list. Every failed line is a
named defect class (`light-source detachment` /
`detached ground glow` in `failure-classes.md`):

1. The source position is declared once, in constants, and every
   light computation imports it.
2. The brightest ground/water pool sits *under* the source, not at a
   convenient composition point.
3. The light path / glint column's x equals the source's x.
4. Every rim and glint is graded by azimuth or distance from the
   source — nearer is brighter, with a declared floor, and attenuates
   smoothly; nothing glows at full strength on the far side.
5. Every luminous mark in the changelog traces back to *some*
   declared source; a scene may have one primary source and at most
   one declared secondary, and each element names which it follows.
6. Forward scatter exists where the brief implies it: warm bleed on
   surfaces near the source's x, not just rim lines.

Auditors find detached glow every time — it is the single most
repeatable light defect in the corpus.

## 3. Blend-mode physics for painters

Blend modes are math, not moods. Picking the wrong one produces
defects that look like composition problems:

- **Screen and dodge are add-only — they cannot darken.** A dark pass
  (deep-water modulation, shading, storm scud) painted with screen
  blend silently does nothing or lightens. Dark passes need a
  **normal-blend** layer with graded opacity.
- **Rim light on near-black needs normal blend too.** Screen on a
  near-black field caps out too dim to read — the rim exists in the
  layer data but never clears the visibility floor. Paint rims
  normal-blend with the azimuth falloff.
- **Multiply is for occlusion** — clouds, scud masses, shadows riding
  on an existing field. Multiply can only darken; it cannot add glow.
- **Dissolve is for grain**: a screened noise layer with dissolve
  gives ambience without smearing structure.
- **Luminosity for tone-only passes**: grade value without shifting
  hue on a certified color field.
- **Filters homogenize hand-built variance** — a wind/stylize pass on
  hand-placed varied marks flattens them into uniform dashes.
  Repaint variance by hand or accept uniformity deliberately (and
  declare it).
- Brush strokes composite toward the stroke's opacity ceiling
  (per-dab flow builds up to it) — a faint-by-intuition opacity
  setting usually renders far fainter than expected. Probe before
  trusting it (see `acceptance.md`).

## 4. Gradient construction

- **Stop planning**: declare the ramp's stops as hex + positions in
  the charter; they are probe targets. A sky ramp typically wants
  3–5 stops, cold→warm, from the zenith down.
- **Exact-stop probe**: sample the gradient's axis at the declared
  position and compare against the declared stop hex. One probe per
  ramp catches value drift that eyes never catch.
- **Dither where banding threatens**: long dark ramps band; a dithered
  fill or a grain pass at low opacity kills the steps. Check with a
  row-mean walk — adjacent-row means should step by ≤1–2 values.
- **Per-band grading**: a gradient inside a band (dune faces, water
  depth) takes a light stop at the light-facing edge and a dark stop
  at the trailing edge, angle along the surface — not one flat fill.
  Flat single-value fills read as paper cutouts.
- **Live gradient layers stay editable**: build ramps as gradient
  fill layers where possible so re-tuning is one set command, not a
  repaint (see `intent-to-tools.md` for the chain).
- **Transparency ramps for fade-outs**: a dedicated shading gradient
  with graded transparency makes reflections dissolve with depth
  instead of terminating at one shared line.

## 5. Accent discipline

- **One temperature family, at most one accent, used once.** A warm
  accent in a cold field is the cheapest reliable focal win; two
  accents is a competition; three is noise.
- The accent is a *budgeted* element like any other: probe its peak
  value and its pixel count, and give it a hierarchy ratio over its
  neighborhood (`grammar.md` §3).
- Build the accent from the piece's own mark language (a stroke fan
  from the source position), never a blurred solid overlay — the
  style-outlier defect lands on the focal element first.
- Accent placement follows the light system: the accent belongs at or
  near the declared source (the lantern, the sun dip), and its
  trailing glow (path, bleed, rim) is part of the same accent budget.

## 6. Luminance floors — dark-on-dark fails on value, not edge

Dark occluders on near-black fields are the most mis-budgeted element
class in the corpus:

- They fail on **value/opacity contrast**, never on edge sharpness. A
  blur cap guards the wrong axis — the lane that is invisible at
  opacity 0.55 is still invisible at hardness 1.0 with blur 0.
- Give every dark-on-dark element an **opacity/contrast spec with a
  numeric floor**: lane probe ≥ local background + the declared value
  steps (2–3 minimum to clear the recognition threshold).
- The failure oscillates if the floor is absent: invisible →
  overcorrected to dominant → "double-streak" → back to invisible.
  The stop criterion (floor AND hierarchy ceiling) must be declared
  before the first fix round.
- The same floor applies to *every* added element, luminous or dark:
  an "added refinement" whose opacity/blur lands below the
  recognition threshold is churn — command layers with no perceivable
  delta. Probe each changelog line's local contrast before the audit.

## 7. Charter checklist (palette & light section)

1. Anchor hexes + positions: the source (with x/y), the ramp stops,
   the accent color.
2. Derivation formulas for every dependent field (water-from-sky,
   mirror, glint, rim falloff, depth attenuation) with their factors.
3. Blend-mode plan per layer: normal for dark passes and near-black
   rims; multiply for occlusion; screen reserved for add-only glow.
4. The light-tracing self-check, signed off before the first audit.
5. Luminance floors for every dark-on-dark element and every added
   refinement.
