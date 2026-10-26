# doc-parse — crop-cascade playbook

How to read a page the single full-frame pass under-reads: partition
the frame into region crops, parse the crops, adjudicate each read,
and compose one analysis. This playbook governs any parse lane that
decides a page needs more than one full-frame read. The parse script
and its config are frozen — the playbook changes how inputs are
prepared and outputs are adjudicated, never the wire contract.

## Why cascade: the recall contrast

- On the reference corpus, full-frame single passes recovered
  12.5–79.3 % of ground-truth strings on dense pages; crop cascades
  over the same frames lifted union transcript recall to 61.5–100 %,
  with judge-verified coverage reaching 100 %.
- The gain comes from the method, not from one lucky crop set: two
  independent cascade implementations on the same frames recovered the
  same ground-truth families and landed within about 12 percentage
  points of each other on every slide.
- Crops buy TEXT, not geometry — crop-local coordinates are unreliable
  for frame placement (Step 5 carries the transform law).

## Decision table — one pass, a re-read, or a cascade

| situation | action |
|---|---|
| Simple page, first read complete and plausible | one full-frame parse at the configured default budget; stop |
| First read finished but suspect (thin on a visibly text-dense page) | corroborate with a different read — a budget change only counts if the transcripts actually differ, else a vision-reader cross-check |
| Full-frame call loops to a truncated finish at every budget | stop re-parsing the full frame; cascade — a region crop carrying an in-crop text anchor ends the loop |
| Dense tables, small text, chart labels, dense or side regions missed | cascade the affected regions |
| Regions exhausted, glyph-floor strings still unread | escalate to a vision reader (Step 4), not more crops |
| A region returns a faithful-empty class block | correct structural omission if the region is textless (Step 4); verify once, never chase |

## When to cascade, when not to

Cascade when:

- the full-frame parse returns any region-class block carrying
  coordinates (`<class_Picture>`, `<class_Chart>`, `<class_Table>`, any
  positioned region) — every such block is a crop order;
- the parse misses dense or peripheral regions, dense tables, small
  text, or chart labels that the page visibly carries;
- the full-frame call loops or truncates regardless of budget — the
  failure is a property of the input form, so change the input form;
- fewer than two usable regions exist — supplement from a judge's
  named defect regions, else full-frame quadrants.

Do not cascade when:

- the page is simple and one read already covers it — a cascade spends
  calls confirming what the first read showed;
- the only open question is transport-level (exit code, finish reason,
  latency) — that is reliability territory, not a content cascade;
- the only "miss" is a genuinely textless region — a faithful-empty
  region class there is correct, not a defect to chase.
## Step 1 — Partition the frame

- Extract every region from the best available full-frame transcript:
  every class block that carries coordinate tokens becomes one crop,
  cut along the region's visual seams (the class-block extent plus the
  margin). An origin-only block (a point, no extent) gets an estimated
  default region box, recorded as estimated.
- Fewer than two usable regions: supplement from a judge's defect list
  (judge-named regions); as a last resort, cut full-frame quadrants.
- Record every crop in a manifest at creation time: id, region class,
  level, source call dir, frame-px box, upscale scale, and the
  crop-to-frame transform. A missing or null box in any manifest row
  is a hard failure of the run.
- Cut each crop from the source image with a small margin (about 4 %
  of the box dimensions, clamped to the frame), upscale (Lanczos, 2–3×)
  so the crop is at least ~480 px wide, and keep it within the
  parser's 1664×2048 input ceiling. Pre-check every crop objectively —
  dimensions and nonzero mean — before parsing.

## Step 2 — The anchor law

- **An anchor-less crop returns an empty `<class_Picture>` with corner
  coordinates and nothing else.** A crop carrying no readable text
  token produces this one-line shell no matter how much visual content
  it holds.
- **One in-crop text anchor unlocks row-level parsing of its
  neighbors.** A stable visible string inside the region — a chart
  title, a table header, a labeled axis — flips the same crop from
  shell to a full structured read.
- **Extra anchors and dense line art crowd the target out.** A crop
  saturated with anchors latches onto one of them and drops the very
  rows it was cut for.
- **Law: size every crop to the target plus exactly one anchor, no
  more.** Choose the anchor from a stable, visibly printed string near
  the target content, never a guessed label. If the read returns the
  anchor plus scaffolding while the target rows still garble, re-cut
  tighter around the target — do not add anchors.

## Step 3 — Parse the crops

- Run each crop through the skill's parse script into its own fresh
  call directory (one directory per call, never overwritten), same
  record convention as full-frame calls.
- **Bounded parallel fan: batch crop parses in one shell invocation
  with background jobs and `wait`, capped at four in flight against
  the one endpoint; refill slots as calls finish.** Measured 2.3–2.9×
  wall-clock speedup with no fidelity loss; mechanics, pacing, and
  retry discipline live in reliability-notes.md. Keep vision-reader
  legs sequential — one in flight — even while parses fan out.
- **The output budget is a dial, not a knob.** `max_output_tokens` is
  measured, not monotone: raising it can change nothing where the
  model self-stops far below the ceiling, and it can sharply regress a
  page — a rich read may exist only at the low default and lose most
  of its recall at a higher ceiling. Keep the configured default
  unless a measured per-crop delta justifies a change; when a crop
  under-reads, try both directions — a lower and a higher budget —
  before concluding the crop is blind. A budget change corroborates
  only when the transcripts actually differ (corroboration law in
  reliability-notes.md).
- A crop whose parse loops to a truncated finish is a failed call:
  bank it with its record, retry once into a fresh directory; if the
  loop reproduces, change the input form (re-cut, re-anchor), never
  the budget.
## Step 4 — Adjudicate per crop

- The crop's own parse transcript is the primary judge. An independent
  vision reader (a vision subagent over the crop image) adjudicates
  everything the parse leaves doubtful: new strings, garbles, missing
  rows. Classify per element: real-and-expected, real-novel,
  hallucination-candidate, ground-truth-gap. The defect vocabulary in
  process-notes.md applies unchanged to crop transcripts.
- **Hard floors — lane-specific; a vision reader does not share them:**
  - letterform or badge glyphs around 15–22 px can stay unread at the
    full frame at any output budget and at every compliant crop scale,
    while a vision reader reads the same pixels cleanly;
  - serif subscript digits of about 4–5 px are unrecoverable by the
    parser at any compliant scale;
  - a label readable at the full frame can still drop at crop zoom.
- After a two-scale failure — unread at the full frame and again in a
  tight crop — route the glyph to the vision reader; stop spending
  crops on it.
- **A textless region returning a faithful-empty region class is
  CORRECT, never a defect.** Verify the textlessness once with the
  vision reader, bank the region's geometry and a structure note, and
  stop cropping it; never book it as a read failure and never recurse
  into it hunting for text.

## Step 5 — Compose one analysis

- Merge every banked transcript for the page — the full frame plus
  every crop — into one composed analysis, deduplicated; identical
  re-passes count once.
- **Positions come only from the crop manifest's transform, never from
  crop-local coordinate tokens.** Crop-local tokens are crop-relative,
  clip to the crop's extent, and often collapse to corner values or
  vanish for interior strings; mapping them with the frame dimensions
  places content wrongly. The transform:
  `frame_x = crop_x / scale + box.x0`,
  `frame_y = crop_y / scale + box.y0`.
  `scale` is cumulative — the product of every hop's upscale from the
  source frame — and `box.x0/y0` is the crop png's top-left corner in
  source pixels; a nested crop cut from a parent crop compounds the
  parent's scale and offsets its origin by the parent-region corner.
- Position-source hierarchy: pixel-adjudicated measurements first;
  vision-reader coordinates mapped through the crop transform second;
  the crop's manifest region box (region-level accuracy only) last.
- Every element line carries its frame position, classification, and
  provenance — which call directory, which crop box. A composition
  whose lines lack provenance is invalid. Order lines top-to-bottom by
  frame y; quarantine hallucination candidates and ground-truth gaps
  into their own sections.

## Recursion — crop until a semantic stop

- A crop whose parse returns further nested class blocks may be
  re-cropped (level2, level3, and so on), until its description yields
  nothing croppable. Recurse too when a child's strings stay garbled
  or merged at crop scale — a semantic trigger, recorded on the edge.
- Stop reasons, recorded per node in the manifest:
  - `leaf` — the crop's parse returns no region or class blocks;
  - `no-internal-structure` — a single simple block with nothing worth
    cropping inside;
  - `too-small` — too small at source scale for a further crop to
    yield anything;
  - `no-new-information` — the child parse adds zero new content
    against its parent (the most common stop);
  - `backstop` — a safety cap was reached.
- **Caps (about 16 crops, about 24 parse calls per page) are
  protection, never targets.** Reach them only where dense content
  demands it; a backstop stop is a signal to escalate remaining gaps
  to a vision reader, not to raise the caps.

## Worked micro-example

A page whose one dense table arrives from the full-frame parse as a
bare `<class_Table>` block, frame box (120, 300)–(840, 500), header
row unread:

1. Partition — one crop from the table block: margin 4 % → box
   (110, 292)–(850, 508); Lanczos 2× → a 1480×432 crop, inside the
   ceiling and over 480 px wide; the manifest records box, scale, and
   transform.
2. Anchor — the column header printed above the table's first data
   column, a stable visible string inside the crop, is the single
   anchor. The rows-only variant of the same crop, anchor-less,
   returns only the empty `<class_Picture>` shell with corner
   coordinates.
3. Parse — the crop parse runs in its own call directory at the
   default budget, batched with sibling crops, four in flight; the
   table comes back row by row.
4. Adjudicate — row strings are classified against the expected
   inventory; cells below the lane's glyph floor that stay unread go
   to a vision-reader leg, not to more crops.
5. Transform back — a cell read at crop-px (200, 120) sits at
   frame_x = 200 / 2 + 110 = 210, frame_y = 120 / 2 + 292 = 352; it is
   never placed at 200/1480 and 120/432 of the frame.
6. Compose — the merged analysis carries the table rows as element
   lines with frame positions, classifications, and the crop's call
   directory as provenance, ordered by frame y among the full-frame
   element lines.

## Automated lane

`scripts/crop_cascade.py` executes this recipe as one run (see
SKILL.md's tooling contract for the full CLI). The flags map to this
playbook's laws: `--max-parallel` is the bounded fan (cap 4 in
playbook terms, hard cap 8); `--max-crops` / `--max-parse-calls` /
`--max-depth` are the budget dials; `--max-retries` feeds both lanes'
retry ladder. Deterministic stop reasons here are exactly this
playbook's: `leaf`, `no-internal-structure`, `too-small`,
`no-new-information`, `backstop`. Genuine non-determinism (new
information, garbled re-cuts) escalates once per node to the chat
adjudicator through the decision template
(`references/prompts/crop_decision.md`) — advisory only: with the
chat lane down, the run completes degraded on conservative CROP
fallbacks, flagged in `manifest.json`. Composition is deterministic
geometry + merge with per-element provenance (the script writes
`composed/<stem>_composed.md`); it is not interpretation — judgment
stays with the caller.
