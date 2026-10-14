# failure-classes.md — the named defect vocabulary

~22 named classes. Each row: **detection cue** (the phrasing auditors
and probes use) → **repair rule** → **fix tier** (1 mark-patch,
2 generator-reseed, 3 grammar-repaint, 4 escalate) → **prevention**
(where the class is stopped at charter/build time).

Phase 1 of the loop imports every matching row into the charter; Phase
5 classifies every finding here before choosing a fix. A class not in
this roster gets named and added — audits mint classes; kickoffs
import them; the skill's judgment compounds across projects.

## A. Grammar and repetition classes

**1. Grammar-subject mismatch** (a.k.a. grammar-subject
misreading, "reads as terrain, not water")
- Cue: the element reads as the wrong subject — "mountain ridgelines
  at night more than ocean waves", "dunes read as paper cutouts".
- Repair: repaint the element in the subject's grammar (curve-based
  for water/clouds, hand-knots for terrain). No lower-tier fix
  touches this class.
- Tier: **3** (grammar-repaint).
- Prevention: name generators after the subject they paint
  (`grammar.md` §1); audit the grammar class in v1, and if flagged
  critical, plan the repaint immediately.

**2. Procedural pitch periodicity** ("picket rhythm", picket
fence, metronomic peaks, sawtooth uniformity)
- Cue: crest gaps measured exactly equal; "regular in pitch",
  "picket-of-identical-triangles", "metronomic peak rhythm".
- Repair: reseed/re-shape the generator — varied segment length,
  mass distribution, jitter, swell, notches, dropout; hand-author
  knots for hero silhouettes. Surface blur and anchor-inserts change
  pitch stats but not the straight-segment register the audit reads.
- Tier: **2** (generator-reseed).
- Prevention: declare a pitch-variance floor per repeated element and
  check the gap list at generation time.

**3. Register outlier** (style-register outlier, pasted-on overlay)
- Cue: "flat airbrush band… glow-filter overlay pasted on"; a crisp
  vector focal in a wash field; a blurred solid where strokes belong.
- Repair: rebuild the element from the piece's own mark language
  (e.g. a warm stroke fan from the exact light point), in place.
- Tier: **3** if the element's whole dialect is imported; **1** if
  only its parameters are off-register.
- Prevention: the charter's medium declaration forbids the opposite
  register up front (`grammar.md` §2).

**4. Register conflict** (three registers fighting, faceted
silhouette in painterly washes)
- Cue: "silhouette curvature must match the fill's register";
  continuity scores collapse while fills and marks are individually
  fine.
- Repair: pick the winning register and repaint the loser's surfaces
  or silhouettes to match it.
- Tier: **3**.
- Prevention: one register per piece, declared frozen at kickoff.

**5. Refinement invisibility** (refinement-invisibility cluster)
- Cue: "its own delta is invisible"; "looks like the last version
  with polish, not the promised additions" — added elements all land
  at/below the recognition threshold.
- Repair: push each named addition over its visibility floor
  (opacity/blur/size), or remove it. Do not ship unprobed additions.
- Tier: **1** (parameter/mark-patch), per element.
- Prevention: every added element gets a luminance/contrast floor in
  the charter (`palette-light.md` §6).

**6. Invisible fix**
- Cue: pixels prove the change happened, but the audit still reads
  the old behavior ("a break one cannot see is a failed fix").
- Repair: push the delta to the auditor's stated bar — ≈2–3 value
  steps vs local background — then re-probe.
- Tier: **1**.
- Prevention: fixes inherit the target element's visibility budget;
  declare the bar with the fix.

**7. Single-element oscillation**
- Cue: five-plus audit rounds on one layer; fixes swing between
  invisible and dominant; hierarchy scores bounce 5→6→6→4→8.
- Repair: after two failed rounds, change the solution's *shape*
  (one bisecting bar → two gapped segments framing the core), and
  apply the declared stop criterion (floor AND hierarchy ceiling).
- Tier: any — the defect is the *process*, not the tier choice.
- Prevention: declare the numeric stop criterion per risky element at
  kickoff; two-strike rule in the charter's iteration rules.

**8. Bead seams / stamp periodicity**
- Cue: repeating bead stamps along a curve; "chunk seams read as
  stamp-periodicity"; uniform dashes reading as "applied stickers"
  or "scattered confetti".
- Repair: vary spacing/size per chunk or paint one overlapping
  continuous stroke; taper runs to nothing at both ends.
- Tier: **2**.
- Prevention: `grammar.md` §6 repetition law at generation time.

## B. Depth and hierarchy classes

**9. Within-band mark dropout** (within-band rim dropout)
- Cue: a light accent drops out on some members of the same band at
  the same angle — the mark family is discontinuous.
- Repair: restore the family with a faint uniform echo on every
  member (same logic, graded only by distance), not spot fixes.
- Tier: **1**.
- Prevention: "attenuate, never zero" — the dialect grading table
  declares a per-band minimum (`grammar.md` §4).

**10. Distance-invariant accent** (distance-invariant light accent)
- Cue: "every band carries the same dash size, brightness, and
  spacing regardless of depth"; rim dialect truncated across bands.
- Repair: re-grade the accent per band — size, opacity, blur, dropout
  all varying with distance.
- Tier: **2** (regenerate the accent's grading table).
- Prevention: depth is declared as value ladder + dialect grading, not
  band count.

**11. Focal inversion**
- Cue: a secondary element (moon, dust lane, teal glow, scud) out-
  contrasts the declared anchor; hierarchy score collapses.
- Repair: dim/split/de-fang the competitor to restore the declared
  hierarchy ratio — usually cheaper than brightening the anchor.
- Tier: **1**–**2** (parameter/grading), unless the competitor's
  grammar itself reads wrong.
- Prevention: a numeric hierarchy-ratio budget probed before the
  first audit (`grammar.md` §3).

**12. Frame vacuum** (half-frame mark vacuum, featureless sky)
- Cue: a frame region (often half the canvas) with no named feature;
  "foreground plain… black matt".
- Repair: add cheap named features exactly where the audits called
  flat — washes, broad low-alpha strokes, small closure sets.
- Tier: **1** (additive mark pass).
- Prevention: the weak-third walk at charter time
  (`grammar.md` §5).

**13. Canvas-edge termination**
- Cue: a hard value step at the frame border; washes visibly cut at
  the edge; "left-edge wedge" artifacts.
- Repair: extend the offending geometry/wash past the canvas (re-path
  or repaint overscanned), removing the visible termination.
- Tier: **1**–**2**.
- Prevention: overscan all geometry and washes past the canvas edge
  at build time.

## C. Light-logic classes

**14. Light-source detachment** (detached ground glow,
light-path-source detachment)
- Cue: ground glow brightest center-left while the source sits upper-
  right; a luminous pool with no traceable source; "fails to connect
  visually to the source".
- Repair: anchor the brightest pool under the source; set the path x
  to the source x; re-grade rims by azimuth falloff with a floor.
- Tier: **2** (the light formula, not individual pixels).
- Prevention: the light-tracing self-check before every audit
  (`palette-light.md` §2).

**15. Screen-cannot-darken misuse**
- Cue: a dark pass that silently lightens or does nothing; deep-water
  rows that never get darker than the flat bottom.
- Repair: move the dark pass to a dedicated normal-blend layer with
  graded opacity.
- Tier: **1**.
- Prevention: the charter's blend-mode plan (`palette-light.md` §3).

**16. Halo seam**
- Cue: "pasted-on glow with hard boundary" at a silhouette base; a
  glow layer whose edge is a visible line.
- Repair: soften the seam (feather/rasterize+blur the glow's edge) or
  rebuild the glow from graded strokes.
- Tier: **1**.
- Prevention: glow beds are blurred strokes or screened washes with
  graded falloff, never hard-edged fills.

## D. Tool-mechanics classes (the art-side of known engine traps)

**17. Filter-on-shape**
- Cue: build dies with "filters need a pixel layer"; planned soften
  silently dropped.
- Repair: rasterize the shape layer in place, then blur with an
  explicit layer id.
- Tier: **1** (process fix, not an art change).
- Prevention: every build script rasterizes before filtering; verify
  `kind` before any filter call. Full trap mechanics →
  photocraft-automation.

**18. Filter-flattens-variance**
- Cue: hand-built varied marks come back uniform after a filter pass
  ("uniform dashes" the audit attributes to laziness).
- Repair: repaint the variance by hand, or accept uniformity
  deliberately and declare it.
- Tier: **2** (regenerate the marks).
- Prevention: budget filters on hand-built variance; prefer per-mark
  variation in the generator.

**19. Noise-as-stars**
- Cue: "grain masquerading as stars"; the starfield reads as film
  grain at review magnification.
- Repair: replace grain with discrete point dabs in size classes —
  or, in fidelity mode, dim it and keep it BY-DESIGN.
- Tier: **2**.
- Prevention: stars are a declared point-class grammar
  (`grammar.md` §1); grain layers are ambience only.

## E. Process and audit classes

**20. Wrong-bytes audit**
- Cue: the audit confidently describes things the export lacks
  ("completely absent") or contradicts the visible render; the round
  ran against a stale or partial build.
- Repair: void the round explicitly; re-export; re-run the audit
  against the recorded bytes.
- Tier: n/a — process.
- Prevention: audit only bytes whose provenance (path + hash/mean)
  was recorded at export; void stale rounds on any rebuild
  (`acceptance.md`).

**21. Degenerate transcript**
- Cue: headers intact, sentences corrupted ("section-shaped token
  salad"); a coherent-looking audit that is garbage; hallucinated
  regions bundled with real findings.
- Repair: verify the transcript's content nouns against the known
  image before adjudicating; re-run once, accept the coherent pass.
- Tier: n/a — process.
- Prevention: every finding is adjudicated against a pixel probe
  before any edit; probes refute hallucinated regions.

**22. Spec drift**
- Cue: the same pixels score as a defect in one version and a
  strength in the next; the audit VIEW header quietly changed
  register language; "the contract moved".
- Repair: restore the original declaration or log the change as an
  explicit scope change in the charter, then restate the audit
  contract and note which past verdicts it invalidates.
- Tier: n/a — process.
- Prevention: the medium declaration and budgets are frozen at
  kickoff; scope changes are declared in notes, never drifted
  between audit headers.

## Using the roster

- **At kickoff (Phase 1)**: scan all 22; import every row whose subject
  class matches into the charter with its prevention rule.
- **At fix time (Phase 5)**: match the finding's cue text first, apply
  the repair rule, and respect the tier — a Tier 3 defect given a
  Tier 1 fix is the most expensive documented failure mode.
- **At audit time (Phase 6)**: label findings REAL / REFUTED /
  DEBATABLE / BY-DESIGN *before* reaching for this roster — a
  hallucinated finding needs no class.
- **New names**: when an audit proposes a vocabulary name that this
  roster describes, adopt the audit's name in your charter notes; when
  it names a genuinely new class, mint it in the same cue → repair →
  tier → prevention shape.
