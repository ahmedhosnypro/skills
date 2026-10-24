# Pipeline — extraction → analysis → validated specs

## Frame extraction

`ffmpeg` at 1 FPS into `<video>/frames/` (gitignored; never re-extract or
re-download the video — the frames directory is expensive). The source video
itself is supplied by the owner: obtaining it is a user-mediated step (e.g.
platforms that block anonymous datacenter downloads need cookies exported from
a logged-in browser session). Where slides are already available as images,
skip straight to dedup or curation.

## Slide dedup (perceptual hash)

Dedup the frame set with perceptual hashing (e.g. Python `imagehash`, hamming
distance threshold 8) into `<video>/unique_slides/`:

- Threshold 8 groups slide-build animations/repeated builds reliably.
- **Keep the LAST frame of each group**, not the first — slides animate into
  their fully-built state; the first frame is a partial slide.
- **Any tool with a small default cap gets that cap stated explicitly on every
  full-deck run** (a real dedup pass defaulted to 10 frames and a truncated deck
  looked like a successful dedup). Sanity-check the produced slide count against
  the video (duration/FPS, slide density) before the review packet.
- Local CPU, deterministic, idempotent — safe to re-run over the whole frame set.
- The dedup pass should write byte-exact copies of the kept frames — which is
  what makes post-curation reconciliation possible (below).

## HARD STOP — human review gate (binding, non-negotiable)

After dedup writes `<video>/unique_slides/`, **STOP THE PIPELINE**. No vision
analysis, no text validation, no DB registration as ready, no build dispatch, no
subagent fan-out on these frames — NOTHING downstream may start until a HUMAN
has reviewed the extracted unique frames and approved the set.

Why: curation is human-owned. A real curation culled duplicates, non-valid
frames ("Processing..." placeholders, number mismatches) and renumbered the
survivors by the printed badge — decisions the machine must never make for
itself or mark approved.

What the machine MAY do while stopped: prepare the review packet only — a
contact-sheet montage and a plain frame list (kept filename, source frame,
timestamp) — and register rows in the progress DB as pending. What it may
NEVER do: write `slides_index.json`, `new2old_mapping.json`, or any other
slide JSON map/index before approval; proceed to analysis or anything
downstream; or set any "approved/ready" marker itself. A pre-approval map is
stale by construction because curation renumbers the set. Resume only on
explicit human approval of the frame set; then write `slides_index.json` ONCE
from the confirmed files in printed-badge order.

## Curation — reconciliation law

Human curations are NOT just deletions. Expect and record the decisions in the
approval notes / review packet (never second-guess):

- **Group splits**: one phash group → two consecutive slides (the sequential
  threshold merged two similar slides; the curator split them back).
- **Frame swaps**: the curator keeps a DIFFERENT frame from inside the slide's
  group (record the swap + the group's original kept frame; phash-diff the pair).
- **Dense renumbering**: survivors are renumbered 1..N — the new file number ≠
  the dedup-order number. Because no slide JSON map exists before approval and
  no downstream artifact has consumed the dedup numbering, the approved set is
  the namespace's single numbering baseline: no new-to-old map is needed.
- **Index timing law**: build `slides_index.json` ONCE after approval, from the
  confirmed files in printed-badge order. Writing a map/index before approval
  is forbidden — curation invalidates it by construction. The normal flow never
  writes `new2old_mapping.json`.
- **Legacy namespaces** already carrying pre-approval artifacts (analyses, DB
  rows, QA dirs from an earlier run) are the one case that needs
  `new2old_mapping.json`: build it AFTER approval from content hashes before
  rebuilding the DB; preserve the old index + DB as evidence; never delete
  old-numbered artifacts — archive them (old analysis dirs, `*.db.bak`, old
  builds, old QA dirs). Resolve a historical "slide N" through that mapping
  before assuming a pre-approval artifact belongs to the current same-numbered
  slide.
- **Recovery when a legacy mapping was never written** (curation left only
  renamed files + a stale index): md5-match each surviving file against the OLD
  GROUPS' kept frames first (that is how the files were created), full-frame
  search only for curator swaps. A naive md5→frame dict silently collapses
  duplicate-content frames (one real deck: 5440 frames → 5215 distinct
  contents) and misattributes timestamps. Assert: every file matched, ≤2 per
  old group, monotonic old sequence; anomalies stop the machine and go to the
  human.
- **Post-approval curation re-opens the gate**: if the confirmed set changes
  after the index/DB exist, archive that index/DB as evidence and rebuild from
  the new confirmed set; write `new2old_mapping.json` only if downstream
  artifacts already exist for the superseded numbering.
- **A namespace containing ONLY curated `unique_slides/` (no frames/index/DB)
  means the owner replaced the pre-approval state** — do not hunt for old
  artifacts or "restore" anything; the owner's confirmed files are the set.
  Build `slides_index.json` once from them, then register.

## Source research (when the project demands verified sources)

A video namespace may carry its own instructions file requiring web-verified
analysis. The full protocol lives in **`references/source-research.md`**: the
per-slide loop (search the primary source → fetch and confirm → save the
source's own figure files), all research under one `sources/` subdirectory
(`sources/slide_NNN_source/` + `SOURCES.md` — **no SOURCES.md = the research
step did not happen**), the fleet-level `SOURCES_MAP.md`, trust discipline
(nothing recorded from an unfetched snippet), the spec-correction protocol
(model annotations only, never frame text), and the discrepancy law (the
frame wins for recreation, the source wins for understanding). It activates
only after the human review gate, interleaves with analysis/validation, and
is never dependency-gated.

## Vision analysis (per unique slide)

One streaming vision call per slide into `<video>/analysis/slide_NNN_raw.json`:

- **Streaming always** (non-streaming requests die as `ServiceTimeout` at
  aggregating gateways' ~60s cut while the pool churns keys — streaming works).
- ~540 tokens/frame at 960px JPEG q4 — budget vision calls accordingly.
- Slow (~3-5 min/slide). Check the log for `finish=stop` per slide;
  `finish_reason=length` with `content=null` + filled reasoning means the model
  spent the whole budget thinking → raise max-tokens.
- Idempotent (skip existing outputs). To retry ONE slide: delete its
  `slide_XXX_raw.json` and re-run range-scoped.

## Text validation

A text-only validation model cross-checks each raw analysis into
`slide_NNN_final.json` (never use the text model for visual checks):

- Empty content / "Expecting value: line 1 column 1" → transient, just re-run;
  the pass retries only missing finals.
- Persistent stalls: the model burns its whole token budget on reasoning →
  raise max-tokens. Some endpoints' completion ceiling is ~32k regardless of the
  request — a spec that dense is a re-analysis problem, not a budget problem.
- **Ranged/filtered runs rewrite the combined `slides_final.json` to ONLY the
  ranged slides** (observed: clobbered to 1 entry; also to `[]`). A "slides N"
  parameter is a COUNT cap (with a small default), not "all". After EVERY ranged
  run, repair by full re-aggregation: no range filter + count ≥ deck size,
  idempotent with zero model calls when all finals exist — sort by slide
  number, `json.dump(finals, f, indent=2)`. Nothing consumes slides_final.json
  before the re-aggregation. Treat it as derived — always rebuildable from
  per-slide finals.

## Content gate (before any build)

Ready iff `validation.verdict ∈ {PASS, PASS_WITH_FIXES}` AND
`validation.recreatability_score ≥ 8`. Otherwise delete that slide's raw+final
and re-run analysis then validation (range-scoped), cap 3 retries, then
report/block with the error in the row's `last_error`. Judge-certified
acceptance of a score-7 slide is a documented deviation, not a silent pass —
record it.

**Before deleting a raw+final for a content-gate re-run**: read the dependency
view and the final's verdict/score FIRST — the buildable set excludes a slide
for THREE causes (content-gate failure, dependency gate, pattern gate), and a
gate-passed slide missing from buildable is usually dep/pattern-gated (correct
behavior), not a spec failure. If evidence must move, copy-then-delete (never
bare rm) so the mistake is reversible.

## Output contract

`slides_final.json` — array of slide objects: `slide_title`, `verbatim_text`
(VERBATIM — no paraphrasing; equations and labels included), `layout`
(arrangement + regions), `visual_elements` (type, chart data values, colors,
position), `imagery`, `colors` (approx hex), `typography_notes`,
`recreation_brief` (numbered checklist), and a `validation` block (verdict,
fixes, `[?]`-marked uncertain items, recreatability score). Uncertain content
keeps its `[?]` marker — never invent facts.
