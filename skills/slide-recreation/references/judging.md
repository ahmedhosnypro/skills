# Judging — the visual verdict law + adjudication

A slide is done ONLY when a real comparison transcript from the vision model
contains a winner-body PASS. Everything else is a FAIL (or a re-try), no
exceptions:

- Timeout / empty stream / probe-only read / degenerate garbage output →
  recorded FAIL.
- A worker's or peer's "looks good" → not a verdict. A PASS obtained without
  the ground rules → re-judge.
- A judge call without the exact `-p` payload is a MISFIRE, not a verdict — the
  gate runs its default prompt, the model answers coherently, and nothing is
  certifiable. Source the payload byte-for-byte from the banked
  `judge_prompt_N.txt` (or write it to a file and `-p "$(cat ...)"`); bank the
  misfire as spent evidence.
- `--view`/`--capture` take VALUES (free text) — a bare flag aborts the whole
  dispatch with an argparse error. Grep the dispatch log for `[error] argument`
  before assuming the model failed.

## Invocation pattern

All vision calls go through a concurrency-limited gate (a flock around your
vision client — fleet-global across all workers/decks; never raw per-call).
Route to the deck's configured vision model; never let a per-call flag silently
switch routes.

Comparison (the real judge):

```
timeout 1700 <vision-gate> timeout 1650 <vision-client> comparison \
    <render_K.png> <original_frame.jpg> \
    --view <banked context> --capture <banked context> \
    --thinking high --max-tokens 65536 --timeout 600
```

- **Walls**: the outer `timeout` wrapper must EXCEED the gate's internal retry
  ladder — ~2× the per-call hard wall (1700s outer validated for `--timeout
  600`; the ladder's 3 internal attempts each ~630s means >1260s of
  gate-internal time). A HangError that fires while the gate is still inside
  its own ladder is a wrapper-budget bug — resize and re-run, don't churn
  attempts. Also: a client's internal abort+retry is trapped INSIDE the outer
  wall — a HangError at the internal wall means re-dispatch the whole command,
  never trust the in-process retry; never pipe the gate without preserving its
  exit code (`| tail` masked a fatal 124 as success).
- **Probe minimal**: open/verify the window with a tiny prompt (`-p "Reply with
  the single word READY"`, short wall). Heavy open-ended analysis prompts make
  the upstream stream `reasoning_content` forever (HangError) even while
  `GET /v1/models` answers — the real judges run at `--thinking high
  --max-tokens 65536` inside the wide wall. Fleet-wide storm gating is in
  fleet.md.
- **W4 retry**: one hard-wall HangError retry is part of the protocol (not an
  attempt).
- **3 garbage re-invokes** allowed (degenerate output = the call didn't
  happen), and **6 judge attempts per slide** before parking the row as failed
  for review.

## The ground-rules prelude (mandatory in the judge prompt)

The judge sees two images (recreation first, original second) and flags
intentional differences as defects — a streak of FAILs on intentional
differences is a prompt bug, not a slide bug. Prepend a GROUND RULES prelude
stating, in the DECK's own terms (describe the deck's measured chrome, never
another family's values):

(a) the house template (frame/badge/title geometry) is intentional — findings
    about it are overridden;
(b) contentless originals are matched by contentless recreations;
(c) lecture-video artifacts (cursors, player chrome, watermarks, capture
    glitches) are correctly OMITTED from the recreation;
(d) typed-vs-handwritten renderings of the same text are MINOR;
(e) equations in the recreation are rendered in PROFESSIONAL 2D FORMAT (stacked
    fractions, large Σ with limits, aligned sub/superscripts) — a linear/typed
    original is a mandated format upgrade, NOT a discrepancy;
(f) the verdict is about fidelity of renderable content only.

End the prompt with: `FINAL VERDICT: PASS or FAIL for 'faithful, usable
recreation'` and require the winner body to name the winning image explicitly.
Bank the template once per deck and use it verbatim (pattern judge-invocation);
keep the `-p` template VERBATIM and carry measured facts in the
worker-editable `--view`/`--capture` context fields.

## Adjudication laws — before any fix or any acceptance

The judge's findings are HYPOTHESES. Adjudicate against pixels before spending
a fix cycle; a wrong FAIL body is evidence of judge variance, not of a defect.

- **PIL over prose, both directions.** Measure every MAJOR against the original
  frame before acting. Refuted MAJORs go into the judge context for the next
  attempt as objective ground truth ("the claimed element does not exist in
  the original"); never edit the build to satisfy a finding PIL refutes.
  Symmetrically, PIL refutes the judge's magnitude estimates too — measure the
  real gap and fix that (a judge eyeballed "~30%" where PIL showed 4%; fix the
  4%).
- **Judge variance is sampling.** The same bytes can flip verdicts across
  attempts (documented: crop FAIL → full FAIL → PASS on identical pixels).
  After refuting all findings, RE-ROLL the same frozen judge on UNCHANGED
  bytes and certify on the clean PASS with an adjudication record for the
  classes still raised. Bank the refuted FAIL transcripts as variance evidence.
  A verdict whose body is coherent but factually false (claims contradicted by
  pixel measurement of the exact crops it saw) is defective evidence like
  garbage — tiny crop canvases push the model into fabrication; measure both
  crops first and rebut with numbers.
- **Sub-10px "absent element" findings are falsifiable in one probe**: check
  whether the build determines the pixels by construction (literal text, shared
  draw function), then PIL-probe the exact band in the FRAME. A judge's
  "absent/truncated" claim at blur resolution often describes ink it merged or
  looked below (a head that sits INSIDE the box, not below it). Truncation
  claims contradicted by a PIL full-span proof are usually stroke-weight
  letter-merging at small sizes, not missing text.
- **"No marks in region X" decisions need relative-ink scans + a baseline
  diff.** Scan with a relative-ink mask per local fill (ink can sit within
  tolerance of its own fill color at frame resolution), never a white/absolute
  mask; and when removal is in question, diff renders before/after the
  questionable change — a known-absent baseline proves presence or absence in
  both images at once.
- **Crop-pair discipline**: (1) crop-vs-crop pairs ONLY — never pass the full
  frame as IMG2 to a crop judge (re-check dispatch argv against the template);
  (2) MATCHED effective scale: compute effective scale = output_px/frame_px for
  BOTH images and make them equal, per-axis when the mapping is anisotropic —
  an 8% mismatch fabricates scale/position drift MAJORs; (3) map every
  crop-relative judge coordinate back to slide space before editing geometry,
  and discard findings that only make sense as a different element.
- **Judge size prescriptions carry resolution-normalization bias** — a 150dpi
  render compared against a 960px original gives render-space size vocabulary.
  Translate numeric prescriptions into the ORIGINAL's own pixel geometry and
  PIL-verify before spending the next attempt.
- **Small-text colors and tiny glyphs: full-frame reads are not evidence.**
  Settle dense-region color with a pixel column-profile of the original BEFORE
  building, and with a 2-3x (up to 5x LANCZOS) crop comparison — crop scale is
  what makes 6px glyphs and 14pt colors legible to the model. When zoom reads
  disagree, PIL ink cores are the final word.
- **Occluded glyphs: sibling-IoU at a ring-arc-located window, never a vision
  read.** A vision read of a hidden glyph hallucinates. Locate the element by
  unoccluded structure (ring arcs identical across sibling frames), print
  per-row ASCII ink maps of a fixed window for the question frame AND
  same-font siblings with known values, compare binarized ink IoU — and never
  accept a confirming measurement whose window was located by a polluted
  heuristic or whose strongest alternative hypothesis was never tested.
- **Inherited/cascade zones are adjudication inputs, not fix triggers.** A
  crop-judge FAIL on a region inherited from a certified parent (identical
  pixels in both frames AND the parent's render) is judge variance per the
  inheritance law — fixing it would break the cascade contract. A real child
  defect is confirmed only when child-frame ink differs from parent-frame ink
  at the same mapped coordinates. House chrome and spec-inherited content on
  graphed variants are likewise never fix triggers — remedied by a clean
  re-judge, never by editing the certified composition.
- **Overriding a judge FAIL with PIL evidence requires the measurement to
  cover exactly the flagged elements in the flagged coordinates** —
  region-adjacent presence refutes nothing; when the override fails, the fix is
  child-local (copy-then-modify), never a parent component touch.
- **The owner's precision mandate: a visible deviation from the original is a
  MAJOR even over a judge PASS.** Owner feedback on placement/geometry
  overrides judges (equations.md alignment law); the owner's defect report —
  not the DB's stale `visual_check` — is the state of record for a reported
  defect. Certification binds to judged pixels, but a measured-dossier audit
  of the certified render against the frame is the backstop: a judge PASS never
  overrules visible pixel evidence.
- **Judge-format anomalies**: prose without a `FINAL VERDICT` line, or a verdict
  re-drawn, is handled by re-dispatching the judge on UNCHANGED pixels and
  certifying the re-draw with a pixel proof (render N vs N+1: 0 px differ, pptx
  md5 unchanged). Non-standard verdict wording ("IMG1 is BETTER") is acceptable
  when the body is structurally complete — a documented caveat, not garbage.
- **Machine checks green + judge FAIL**: pixel-verify each MAJOR before
  reacting — judges misread low-quality originals as template deviations
  (chrome shade, line span, caption stagger all disproven by direct measurement
  on real slides), and identical shared-scene features have scored MAJOR on one
  slide and MINOR on its sibling. Disproven MAJORs become judge context; the
  episode is documented in the close-out report. A probe failure after a landed
  comparison is window-opening overhead, not evidence — bank the run log +
  winner body, note the probe failure.

## Verdict handling

- PASS from a real winner body → bank transcript, set `visual_check=PASS`.
- FAIL with findings → adjudicate (above), apply measured fixes, re-render,
  re-judge, increment attempt number.
- Keep counting; at 6 attempts park the slide and report — never silently drop
  it.
- **Identify the certified render by MEASUREMENT, not attempt numbering** —
  judge files don't name their render and attempts/renders number
  independently. Render the current deliverable and PIL-diff against ALL
  numbered candidates: the certified render is the one with diff_px=0 (also
  proves the on-disk deck still serves the certified pixels). mtime pairing
  only confirms the pick.
- Keep per-slide attempt evidence complete: `judge_prompt_K.txt` +
  `judge_attempt_K.txt` (transcript) + render binding. A prompt banked without
  a transcript is not a spent attempt.

## Judge limitations to remember

- Judges misread small numerals (a badge "19" read as "16") and hallucinate on
  occluded/dense content — those findings are adjudication inputs (above),
  never verdicts by themselves.
- A judge PASS does NOT override measured geometry (equations.md alignment law)
  or owner rulings.
- "Low-medium confidence" findings about template/border shades are
  pre-existing MINORs — read the transcript, don't react blindly.
- The full-slide judge CANNOT see delimiter/stroke-level defects (double-
  stroked arcs passed it twice) — dense regions get their own zoomed crop
  certificates (pattern dense-region-crop-compare).
