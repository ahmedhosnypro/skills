# acceptance.md — budgets, probes, adjudication, certification

"Check by pixel comparison, not by eye" is the prime directive. This
file turns it into machinery: budget templates per element type, probe
patterns on the exported PNG, the visibility bar, the adjudication
flow, and the certification law.

## 1. Budget templates per element type

Every named element in the charter gets exactly one budget line, with
numbers. Pick the template that matches the element's type:

**Luminous element** (sun disc, moon, lantern, glow bed)
- Peak value: "disc center reads ≥ #fff0d0 at (x, y)".
- Contrast vs local background: "≥ 3 value steps above the sky at the
  same x".
- If the source sits behind a silhouette, carve the dip first and
  probe the exposed fraction.

**Contrast change / visibility of a fix or addition**
- Before/after delta at fixed coordinates: "row means mid 39.8 →
  bottom 41.1 is sub-visible; the bar is ≥ 2–3 value steps".
- Pixels-above-threshold count for the changed region.

**Gradient / ramp**
- Exact-stop probe: "stop at (x, y) equals #5c2a5e".
- Banding check: adjacent row-mean steps ≤ 1–2 values.

**Geometric mirror**
- Per-knot coordinate check: "reflection y == 2·horizon − source y".
- Symmetry: sampled source/reflection pairs within tolerance.
- Dissolve check: "reflections fade with depth via the declared ramp;
  no shared termination line".

**Hierarchy**
- Ratio budget: "anchor probe ≥ competitor probe × ratio" at fixed
  coordinates (peak luminance, saturated-pixel count, or contrast
  delta — one metric, declared).

**Rhythm / repetition**
- Pitch variance: "crest-gap std ≥ floor" (exact-equal gaps fail).
- Dropout rate per band within the declared range.

**Texture / ambience**
- Region delta: "mean/stdev above the empty-sky baseline by the
  declared amounts, with no visible stamp grid".

**Dark-on-dark occluder**
- Value floor: "lane probe ≥ local background + N value steps"
  (never a blur cap — dark-on-dark fails on value, not edge;
  `palette-light.md` §6).

## 2. Probe patterns — cheapest first

All probes run on the flattened export (or the in-session composite)
— never on layer thumbnails or memory of what was painted:

1. **Point samples**: fixed (x, y) → expected hex. One per declared
   stop, source, and anchor.
2. **Region means**: rectangle means/stdevs before and after a change.
3. **Pixels-above-threshold**: count in a region (whitecap coverage,
   star density, glow spread).
4. **Edge-profile ramps**: walk a line across an edge — a 1–2 px cliff
   vs an 8 px ramp is the difference between a seam and a grade.
5. **Row-mean walks**: banding and value-ladder checks across the
   frame.
6. **Before/after deltas**: the same probe list, two exports — this
   is how a fix is proven, not by re-audit.
7. **Structure probes** (in-session): the layer tree — count, names,
   blend, opacity against the charter. A green scripted run can be
   missing whole layer groups; structure is the acceptance test, not
   exit codes.

Probes are pre-registered: the budget list *is* the probe list. An
element without a probe is not done, and a change without a probe is
not a fix.

## 3. The visibility bar

- An element (or a fix) clears recognition at **≈2–3 value steps**
  over its local background, measured on the export.
- Below the bar, the element reads as absent no matter what the layer
  data says: **an invisible fix is a failed fix** even when
  pixel-proven.
- Faint layers under heavy blur plus screen blend collapse faster
  than intuition suggests — always probe, never estimate opacity by
  feel.
- The bar is part of every budget: any element the changelog names
  must clear it before the first audit, or it is churn.

## 4. Adjudication flow

Every audit finding follows the same five steps, in order:

    finding → probe → verdict → fix-tier assignment → re-probe

1. **Probe first.** Find the cheapest probe that could falsify the
   finding. No probe, no verdict — an unprobed finding is an opinion.
2. **Verdict, exactly one label:**
   - **REAL** — the probe confirms it. Classify
     (`failure-classes.md`), assign a fix tier, fix the cause not the
     symptom.
   - **REFUTED** — the probe contradicts it (hallucinated region,
     misread physics — a "wind contradicts the brief" flag that the
     brief's own physics answers). Record the measurement; log the
     refutation; do not edit.
   - **DEBATABLE** — plausibly intentional or below the visibility bar.
     Log with evidence, leave it, move on; churn stays proportional
     to severity.
   - **BY-DESIGN** — the charter declared this trait up front
     (fidelity targets, deliberate uniformity, faithful-to-reference
     traits). Valid *only* when the contract said so — never minted
     retroactively to please an audit.
3. **Fix-tier assignment** (REAL only): mark-patch →
   generator-reseed → grammar-repaint → escalate, per the failure
   class. Stop after one failed lower-tier attempt against a named
   ceiling.
4. **Re-probe** the targeted criteria, then re-audit. Order REAL
   fixes by severity × cheapness; one modify pass per audit round.
5. **Record the verdicts** (a finding ledger): prior-defect verdicts
   carried into the next audit's prompt as resolved/partial/unresolved
   per element.

## 5. Certification law

- **Provenance**: record the export path plus hash (or mean) at export
  time; audit exactly those bytes. On any rebuild, void stale audits
  explicitly and re-run — a wrong-bytes audit is worse than no audit.
- **Transcript sanity**: verify the audit's content nouns against the
  known image before adjudicating; a structurally well-formed but
  incoherent transcript is garbage — re-run, do not mine it for
  findings.
- **Single-read labeling**: label each certificate with model, route,
  and read count; single-model certificates swing (same geometry
  scoring 7 then 4 across adjacent versions), so treat composite
  deltas of a few points on unchanged regions as noise and steer by
  **resolved-defect counts** instead.
- **Certify late, then stop.** The final gate settles low-severity
  model-residuals with cheap pixel probes — accept, label
  hallucination, or bank — not by reflexive re-edits or re-audits.
- **Post-certification freeze**: any edit after certification voids
  the certificate. If a post-certification probe fails, either re-open
  the loop deliberately (new audit round, new certificate) or ship
  with the residual documented.
- **The spec never moves**: medium, hierarchy, and budgets change only
  as declared scope changes in the charter, never to match the pixels
  (see `spec drift`, `failure-classes.md`).

## 6. Worked micro-case (how the flow reads in practice)

A dawn lake mirror, adjudicating one audit round:

- Charter budgets: horizon y = H; water = darken(sky, 0.78)/desat 0.18;
  mirror = y → 2H − y; "light path x == sun x"; "verify by pixel
  comparison, not by eye".
- Probe results: sun disc ≥ #fff0d0 at the source ✓; light-path mean
  above off-path baseline ✓; crest-rim probe below the rim floor ✗.
- Audit finding "picket ridge rhythm" → crest-gap std probe confirms
  equal pitch → **REAL**, class `procedural pitch periodicity`,
  Tier 2 → reseed the ridge generator with varied pitch/mass +
  feathered rasterize, one pass.
- Audit finding "floating mauve echoes" → probe shows far-ridge
  reflections showing through near-ridge valleys → physically
  consistent with the mirror rule → **DEBATABLE**, logged, kept.
- Audit finding "rim light missing on far crests" → probe shows rims
  at the azimuth floor, above the visibility bar → **REFUTED** with
  the measurement.
- Re-probe the rim and rhythm budgets; re-audit; certify when every
  budget passes and the verdict log is clean.
