# intent-to-tools.md — routing table and field-proven chains

Two halves: (A) the intent→family routing table — which mind-map family
and which search phrases answer each intent class; (B) field-proven
command chains for the recurring intents of naturalistic scene
artwork — each chain intent → commands → acceptance probe.

The search index owns full params and traps; chains here anchor command
ids and the order that worked, not syntax. Run every lookup from this
skill's root: `python3 indexer/mind_index.py search "<query>"`.

## A. Intent → family routing table

Pick the row, then search the phrase (all phrases verified to hit);
browse the family md when the CLI is unavailable.

| Intent class | Mind-map family | Search phrases that hit | Anchor commands |
|---|---|---|---|
| Smooth ramps (sky, water, dune faces) | gradient-fill | "editable sky ramp", "live gradient re-tune" | `gradient.fill.create`, `gradient.fill.set`, `layer.newFillLayer.gradient` |
| Painterly marks (strokes, washes, dabs) | paint | "soft stroke opacity flow", "seeded dab" | `paint.stroke` |
| Silhouettes / terrain / hero shapes | shape-path, layer | "vector silhouette path", "rasterize shape" | `shape.create`, `shape.edit`, `layer.rasterize.shape` |
| Glow beds / atmosphere / soften | filter-blur | "soft glow bed", "depth-graded softness", "linear smear" | `filter.blur.gaussianBlur`, `filter.blur.motionBlur`, `filter.blurGallery.tiltShift` |
| Light accents (flares, relight) | filter-other | "lens flare at light source", "relight scene" | `filter.render.lensFlare`, `filter.render.relight` |
| Tonal grading | adjust-image | "adjustment layer grade", "curves per channel" | `layer.newAdjustmentLayer.*` |
| Regional repaint / masking | edit-selection | "repaint selection in place", "feather selection edge" | `select.sky`, `select.colorRange`, `select.modify.feather`, `edit.clear` |
| Starfields / discrete points | paint | "tiny hard dot dab" | `paint.stroke` (small size, high hardness) |
| Reflections / mirror work | filter-blur, edit-selection | "water reflection smear", "mirror reflection darker" | `filter.blur.motionBlur`, `edit.transform.flipVertical` |
| Structure verification | session-jobs | "composite pixel probe", "layer tree inspect" | `document.pixel`, `document.inspect` |

Routing law: resolve the intent through the index *before* writing
any plan step; verify the chosen id with a follow-up exact-id search
before committing it to the plan.

## B. Field-proven chains

Each chain: the intent as charter language → the command sequence that
realized it (with the craft parameters that mattered) → the probe
that closed it. All chains assume seeded randomness and captured layer
ids (charter discipline).

**1. Sky gradient (smooth ramp)**
- Chain: `gradient.fill.create` — vertical, from the top of the
  frame to the horizon (or full height), 3–5 declared stops cold→warm;
  keep it a live gradient fill so re-tunes are `gradient.fill.set`,
  not repaints.
- Probe: exact-stop check at the declared coordinate; row-mean walk
  shows ≤1–2 step banding.

**2. Mirror reflection (water mirrors the source)**
- Chain: build the source's knot table → mirror it (y → 2·horizon − y)
  in the build script → `shape.create` with the mirrored path at
  ~0.5 opacity → dissolve with depth via a shading `gradient.fill.create`
  carrying transparency ramps → optional smear pass (chain 14).
- Probe: per-knot mirror check (reflection y == 2·horizon − source y);
  reflections fade with depth, no shared termination line.

**3. Sun glint path (light column on water)**
- Chain: N-segment stroke loop — `paint.stroke` per segment, size
  growing with depth, opacity tapering by the declared ramp, x = source
  x + seeded wobble, screen blend, then `filter.blur.gaussianBlur`
  (small). Segmented beats one hard ribbon — "avoids hard-column
  stamp look".
- Probe: path mean well above the off-path baseline at the same rows;
  segment sizes follow the declared ramp.

**4. Rim-lit crests (light graded from the source)**
- Chain: per-segment `paint.stroke` along each crest, brightness
  graded by azimuth falloff from the source with a floor; **normal
  blend** — screen caps out too dim on near-black to read; vary
  size/opacity per run (no uniform wire).
- Probe: rim value ≥ floor + visibility steps at the nearest crest;
  values fall smoothly with azimuth distance; no dropout within the
  band.

**5. Discrete starfield**
- Chain: per-star single-point `paint.stroke` dabs, 2–4 size classes
  (sub-pixel to ~4.5 px), high hardness, seeded RNG placement, an
  exclusion halo around the brightest star. Grain ambience (if any)
  is a separate `layer.new.layer` + `edit.fill` + `filter.noise.addNoise`
  pass at low screen opacity — noise is never the starfield.
- Probe: pixels-above-threshold count per size class; brightest
  star's halo respected.

**6. Depth-graded silhouette bands (ridges, dunes, waves)**
- Chain: per band — `shape.create` with a hand-authored knot table
  (varied pitch/mass, horizon gaps) → fill as a per-band gradient
  (light stop at the light-facing edge, dark at the trailing edge,
  angle along the surface) → `layer.rasterize.shape` →
  `filter.blur.gaussianBlur` graded by depth (far bands softer).
- Probe: per-band value ladder follows the declared stops; crest-gap
  std above the variance floor; no two bands share a pitch frequency.

**7. Waterline mist**
- Chain: `paint.stroke` band on the waterline — sizes ~22–44, hardness
  0, cool color, `filter.blur.gaussianBlur` 12–16; keep the band
  gapped, not one solid stripe; add a few warm bridge strokes where
  the sun contacts.
- Probe: band reads continuous at band level with gaps; sun-to-water
  light bridge present at the source's x.

**8. Warm focal beam with occlusion breaks**
- Chain: focal = a stroke fan — `layer.new.layer`, then warm strokes
  radiating from the exact lantern point (+2 apex strokes on the
  core), `filter.blur.gaussianBlur` small; occlusion = a "break"
  layer of dark swales, **multiply** blend, opacity ~0.5–0.8 with
  blur, placed where foreground swells cross the beam.
- Probe: breaks read at ≥2.5 value steps against the beam ("a break
  one cannot see is a failed fix"); beam apex hot at the source point.

**9. Dark-water modulation (kill the flat bottom)**
- Chain: `layer.new.layer` + `paint.stroke` dark runs in **normal**
  blend (screen cannot darken), graded low opacities (~0.08–0.18),
  seeded variation.
- Probe: region mean below the unshaded baseline by the declared
  steps; no flat single-value expanse.

**10. Ceiling masses (scud, storm clouds)**
- Chain: `layer.new.layer` + `paint.stroke` masses → **multiply**
  blend, heavy blur; a highlight pass on a second layer, screen blend,
  blurred; never leave unblurred strokes inside the blur field (crisp
  marks in a soft field read as self-inflicted).
- Probe: upper-region mean drops by the declared amount; no hard
  scud-band seam at the horizon shelf.

**11. Whitecap dabs**
- Chain: hand-placed clustered `paint.stroke` dabs on crest tops,
  varied sizes/opacities, seeded; **no stylize/wind filter pass** — it
  flattens hand-built variance into uniform confetti.
- Probe: above-threshold pixel count grows to the declared coverage;
  dabs varied, not hard-ended uniform dashes.

**12. Foreground closure set (the last +1)**
- Chain: small named features placed exactly in the regions prior
  audits called flat — shore mounds (`shape.create` + rasterize),
  reeds as short 3-point `paint.stroke` marks with sun-tipped ends,
  bird chevrons, altitude-faded star dabs, post-blur sparkle glints.
- Probe: each named feature reads above the visibility floor in its
  target region; corners closed deliberately.

**13. Glow bed (nebula wash, moon glow, atmosphere)**
- Chain: large soft `paint.stroke` marks, hardness 0, sizes ~300–700,
  `filter.blur.gaussianBlur` heavy, **screen** blend at declared
  opacity — calibrated against a luminance floor, never intuition
  (faint-by-feel renders ~4× too faint under blur + screen).
- Probe: core mean / pixels-above-threshold meet the charter floor
  before the first audit.

**14. Painterly smear pass (reflections read as water, not flips)**
- Chain: `layer.rasterize.shape` on the reflection layer →
  `filter.blur.motionBlur` along the vertical (angle 90°, small
  distance) — the smear reads as painterly water where a hard mirror
  flip reads as stamps.
- Probe: reflection edge profile shows a ramp, not a cliff; smear
  uniform along the column (no bead seams).

## Using the chains

- Chains are starting points: the *budgets* (probe lines) are the
  contract; the craft parameters are field-proven defaults to vary
  deliberately, not silently.
- When a chain's step is rejected by the engine (e.g. a filter
  refusing a shape layer), rasterize in place and retry — trap
  mechanics belong to `photocraft-automation`.
- When a chain's result misses its probe twice, change the solution's
  shape (chain variant) rather than nudging parameters — two-strike
  rule (`failure-classes.md` §A7).
