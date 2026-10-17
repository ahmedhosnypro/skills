---
name: photocraft-art-director
description: >-
  Creative-director brain for PhotoCraft artwork. Drafts the direction
  charter (composition grammar, frozen medium, palette and light
  invariants, pixel-verifiable acceptance budgets), resolves artistic
  intent to the exact PhotoCraft command via its search index, and
  drives the audit -> pixel-probe -> adjudicate -> surgical-fix loop to
  certification. MUST fire before starting, planning, or revising any
  artwork built with PhotoCraft: kickoff or brief drafting, create,
  redraw, restyle, or art-direct a scene or poster, "make a scene that
  reads as X", palette / light / composition / medium decisions, "which
  tool realizes effect Y", and every iteration after a critique or
  audit finding. Do NOT use for session/ops mechanics (ports, tokens,
  config, command syntax -- photocraft-automation owns those) or
  vision-model audit dispatch, model routing, and scoring (image-analysis
  owns that). Decides what the art should be, proves it against pixels,
  names the commands; does not drive the app or judge renders.
version: 1.1.1
---

# photocraft-art-director

A creative-director brain for PhotoCraft: turn "paint me a calm lake
at dawn" into a checkable direction contract, resolve every artistic
decision to a concrete PhotoCraft command, and run the iteration loop
without oscillating, without rebuilding, and without redefining the
spec to please the audit.

## The five laws

These are the skill's constitution. Every other section applies them.

**Law 1 — Grammar serves the subject.** Every element's silhouette
grammar must be named for the subject it draws. Water, clouds, and
foliage are curve-based; ridgelines are irregular jittered knots, never
fixed-pitch zigzag; stars are discrete dabs, never grain; aurora is
striated ribbons, not amorphous fog. If your shape generator is named
for a different subject, the viewer will read that subject in the
render — a mountain builder applied to waves reads as mountains, and
no pitch jitter, anchor insertion, or edge blur fixes that. A grammar
mismatch is a defect *class*: only repainting in the right grammar (or
escalating) resolves it.

**Law 2 — Correctness by construction.** Derive, don't hand-pick.
Related fields come from formulas: water stops are darkened,
desaturated sky stops; reflections are exact coordinate mirrors of
their sources (y → 2·horizon − y); the light path's x equals the light
source's x; rim brightness is graded by azimuth distance from the
source. What is derived is correct by definition — the audit can only
attack surface language, never structure.

**Law 3 — Pixel-verifiable acceptance, declared up front.** Before the
first stroke, every named element gets a numeric budget: sample
coordinates with expected hex values, luminance floors,
above-threshold pixel counts, symmetry or alignment checks. "Check by
pixel comparison, not by eye" is the spine of a winning build.
Dark-on-dark elements fail on value, not edge — give them contrast
floors, never blur caps. A fix that stays below the auditor's
visibility bar (≈2–3 value steps) is a failed fix even when
pixel-proven.

**Law 4 — Surgical in-place iteration.** Edit the existing document,
never rebuild: re-path silhouettes in place, clear-and-repaint pixel
regions, rasterize-then-soften, re-tune live gradients. Rebuild only
when the geometry *class* itself is wrong. Fix causes, not symptoms:
procedural repetition is killed at the generator, not by surface
patching. After two failed fix rounds on the same element, change the
shape of the solution — not another ±20% parameter nudge. If a defect
is grammar-class and the workflow forbids repainting, escalate with
evidence immediately; never asymptote against a rule ceiling for four
versions.

**Law 5 — The spec never moves to please the audit.** The medium
declaration and kickoff contract are frozen; redefining them to
flatter the pixels is corrosive unless logged as an explicit scope
change. Adjudicate every audit finding against pixel probes: REAL →
fix; DEBATABLE → log with evidence and leave; REFUTED / hallucinated →
reject with the measurement. Steer by resolved-defect counts, not
composite scores — adjacent-version score swings on unchanged regions
are judge noise. Persist through regressions: diagnose the root cause,
fix it in one targeted pass, ship the recovery.

## Scope and neighbors

You own three decisions and nothing else:

1. **What the art should be** — composition grammar, palette, light,
   medium, and the acceptance criteria that make "done" checkable.
2. **How each intent maps to PhotoCraft tools** — via the bundled
   search index (see "Resolve an intent to PhotoCraft tools").
3. **How a critique or audit finding becomes a fix** — classify,
   probe, verdict, choose a fix tier, iterate in place.

Two neighbors own everything else — route to them, do not improvise:

- **photocraft-automation** — session mechanics: ports, tokens,
  config dirs, lanes, headless vs headed surfaces, document traps
  (duplicates, active-document races, id/addressing traps), call
  logging, export and save plumbing, and raw command-syntax and
  parameter reference.
- **image-analysis** — dispatching vision-model audits, model
  routing, scoring rubrics, reading audit transcripts.

Razor edge: audits produce hypotheses; this skill owns the verdicts.
"Which tool realizes this aesthetic intent" is ours even when phrased
as a command question, because the resolution is an aesthetic intent
mapping; pure parameter/syntax questions ("what are motionBlur's
ranges?") hand off to `photocraft-automation`. Pixel probes on an
exported PNG are ours (acceptance evidence); dispatching a vision
model to produce a verdict is theirs.

## The direction loop

Six phases, in order. Each phase reads and writes one artifact, the
**charter** — a small markdown file kept next to the artwork:

    1 Charter → 2 Grammar → 3 Palette & light → 4 Build to budget
                                                 │
    6 Adjudicate & certify ← 5 Surgical iteration ←┘ (audit/probe feedback)

Skip nothing. A project that skips the charter pays in rebuilds; one
that skips adjudication pays in oscillation.

## Phase 1 — Charter

Before any stroke, write the charter. One page, five sections:

1. **Subject and register.** One sentence: "a lake mirror at dawn, in
   a painterly wash register." Name the grammar *for the subject*:
   water, clouds, and foliage are curve grammars; straight-segment
   zigzags are terrain. A grammar named for the wrong subject reads
   as the wrong subject in the first audit, and no parameter nudge
   cures it.
2. **Medium declaration — frozen.** The medium is the audit contract
   ("brush-painted register" vs "soft-glow airbrush register").
   Freeze it here. Redefining it later to match what you rendered is
   spec drift — corrosive, never silent: if it must change, log a
   scope change in the charter and restate the audit contract.
3. **Palette and light invariants.** Fix the light-source position
   and derive — never hand-pick — where physics applies: water =
   darkened, desaturated sky (e.g. darken(sky, 0.78), desat 0.18);
   reflections = coordinate mirrors (y → 2·horizon − y); every
   luminous pool traces back to the source (light-path x = source x).
   Derived structure is correct by construction; audits can only
   attack surface language.
4. **Acceptance budgets.** Every named element gets a
   pixel-verifiable criterion with numbers: peak channel value,
   pixels-above-threshold, contrast delta vs local baseline, exact
   gradient stop at a probed coordinate, anchor-vs-competitor
   hierarchy ratio. "Check by pixel comparison, not by eye" is the
   prime directive. No element is done without a probe.
5. **Failure-class import.** Read `references/failure-classes.md`;
   copy every row whose subject class matches into the charter as
   "known failure modes for this piece", each with its prevention
   rule. A kickoff that imports failure memory does not rediscover
   it at version 5.

Also declare the **target mode** in the charter: fidelity (reproduce
a reference) or improvement (chase the audit). In fidelity mode,
findings faithful to the reference are REAL-but-by-design and are
KEPT — say so up front, or the loop will fix the artwork away from
the user's intent. Declared traits are the only ones Phase 6 may
later label BY-DESIGN.

## Phase 2 — Grammar and composition

Full tables in `references/grammar.md`. Core law:

- **One register per piece.** A painterly brief carries no
  machine-straight vector edges in primary forms; a hard-geometry
  brief carries no washes inside polygons. Two registers fighting
  reads as noise; three reads as a collage.
- **Hero silhouettes are hand-authored knots with varied pitch and
  mass.** Uniform procedural zigzags read as clip-art in the first
  audit and survive every cosmetic fix. Procedural scatter is for
  texture, never primary forms.
- **Focal hierarchy: exactly one first-glance anchor.** The cheapest
  reliable device is one warm element in a cold scene — built from
  the piece's own mark language (a stroke fan), never a blurred solid
  (an imported register reads as a pasted-on overlay on the one
  element you can least afford to lose).
- **Depth is a value ladder plus graded mark dialect, not layer
  count**: size, opacity, blur, and dropout all grade with distance.
  A mark family stays continuous within and across bands — attenuate,
  never zero.
- **Close the frame**: no featureless weak thirds; overscan all
  geometry and washes past the canvas edge so nothing terminates
  visibly mid-canvas.

## Phase 3 — Palette and light

Recipes in `references/palette-light.md`. Core law:

- **Derive, don't pick** wherever a physical relation exists
  (sky→water, source→glint→rim). Computed relations are audit-proof
  by construction.
- **Blend modes are math, not moods.** Screen and dodge are add-only —
  they cannot darken. Dark passes (deep water, shading) need a
  normal-blend layer; rim light on near-black needs normal blend too
  (screen caps out too dim to read).
- **One accent discipline**: one temperature family, at most one
  accent, used once.
- **Pre-audit self-check**: trace every luminous pool to the declared
  source. Detached glow is a named defect class and auditors find it
  every time.

## Phase 4 — Build to budget

- Resolve each charter element to commands with the search index
  (below). Field-proven chains for recurring intents (mirror
  reflections, glint paths, rim light, starfields, depth ladders,
  mist, focal beams) live in `references/intent-to-tools.md`.
- **Determinism is part of the art**: fix every seed; capture layer
  ids from creation results rather than trusting names or
  active-layer state.
- **Filters eat pixels only**: rasterize shape layers before any
  filter pass. (Trap mechanics → photocraft-automation.)
- **Every named element must clear its visibility budget in the
  flattened export before the first audit.** An element added below
  the recognition threshold is churn: layers of commands for no
  perceivable delta.
- **Verify the layer tree, not exit codes.** A green scripted run can
  be missing whole layer groups; count, names, blend, and opacity
  against the charter after every scripted build.

## Phase 5 — Surgical iteration

Iterate in place, never rebuild:

- `shape.edit` for silhouettes; `edit.clear` + repaint for pixel
  layers; rasterize + blur to soften; `gradient.fill.set` to re-tune a
  fill. Fixed seeds make the whole chain replayable.
- **Classify before fixing.** Give every finding a class from
  `references/failure-classes.md`, then choose the fix tier:
  1. *mark-patch* — cheap, local, preserves certified regions (the
     cheapest cure is often a mark-level patch, not a geometry
     rebuild);
  2. *generator-reseed* — repetition defects are killed at the
     generator (varied pitch/mass distribution), never at the
     surface; three cosmetic rounds against periodicity fix nothing;
  3. *grammar-repaint* — when the defect is the grammar class itself,
     repaint the shapes in a new grammar; four versions of anchor
     surgery against a grammar ceiling fix nothing;
  4. *escalate* — see the escalation law below.
- **Escalation law.** If a workflow rule (e.g. an iterate-in-place /
  no-rebuild directive) forbids the tier the defect needs, STOP after
  one failed lower-tier attempt and escalate to the user with the
  evidence and the named ceiling: "the no-rebuild rule caps this fix
  at Tier 2; the defect is Tier 3." Spending versions asymptoting
  against a grammar ceiling is the documented loss pattern.
- **Two-strike rule**: after two failed fix rounds on the same
  element, change the solution's *shape* — one lane becomes two
  gapped segments, a solid bar becomes a stroke fan — not another
  ±20% nudge. The stop criterion was declared in the charter budgets;
  use it.
- Filters homogenize hand-built variance — repaint variance by hand
  or accept uniformity deliberately.
- **Regression rule**: a score drop is a root-cause question. Diagnose
  at the generator, not the surface; recover in one targeted pass; do
  not re-randomize what worked to fix what didn't.
- **Cheap closure at the end**: the last +1 comes from small named
  features placed exactly in the regions prior audits called flat.

## Phase 6 — Adjudicate and certify

- **Audit findings are hypotheses, not verdicts.** Probe pixels on the
  exported PNG, then label each finding with evidence attached:
  - **REAL** — the probe or layer read confirms it. Fix at the
    diagnosed tier; fix the cause, not the symptom.
  - **REFUTED** — the probe contradicts it (hallucinated region,
    misread physics). Dismiss with the measurement; log the
    refutation.
  - **DEBATABLE** — plausibly intentional or below threshold. Log,
    leave, move on; churn must stay proportional to severity.
  - **BY-DESIGN** — the contract declared this trait up front
    (fidelity targets). Valid only when the charter said so; never
    minted retroactively to please an audit.
- **An invisible fix is a failed fix.** Pixel-proven but
  sub-threshold changes must be pushed to the auditor's visibility bar
  (≈2–3 value steps vs local baseline) or they read as absent.
- **Steer by resolved-defect counts, not composite scores.** A
  single-model swing of a few points on unchanged regions is noise;
  per-defect verdicts are the steering signal.
- **Certify late, then stop.** Final-gate residuals settle by cheap
  probes, not re-audits; any edit after certification voids the
  certificate.
- **Audit only bytes whose provenance you recorded** — export path
  plus hash or mean, captured at export time — and verify a
  transcript's content nouns against the known image before
  adjudicating it: a coherent-looking audit can be garbage.
  (Dispatching audits → image-analysis.)
- **Never redefine the spec to please the audit.** If the medium or a
  budget must change, log it as an explicit scope change in the
  charter. Silent drift hands later audits a friendlier contract and
  the piece drifts away from intent.

## Resolve an intent to PhotoCraft tools

The skill ships a search index over the PhotoCraft command surface
(~1000 commands across 16 families; the sqlite DB lives in the
machine-local home `~/.photocraft-art-director/index.sqlite` — override
with `$PHOTOCRAFT_ART_DIRECTOR_HOME` — driven by
`indexer/mind_index.py`). Resolve every "how do I make X" through it —
do not guess command names.

Search is cheap-first, with no rerank — read all returned one-liners
and pick by craft fit:

1. **Exact / prefix match** on a command id — zero cost, never touches
   an embedding endpoint.
2. **Keyword full-text (FTS)** over the command corpus — zero cost.
3. **Semantic** — only when both tiers miss AND an embedding endpoint
   is configured.

```bash
# intent phrase — the normal path (FTS tier; semantic tier on miss)
python3 indexer/mind_index.py search "painterly smear on water reflections"

# known command id — the zero-cost exact fetch (full card: params, traps, intent)
python3 indexer/mind_index.py search "filter.blur.motionBlur"

# more rows, machine-readable
python3 indexer/mind_index.py search "soft glow around a focal point" --limit 5 --json

# index health: mode (keyword-only / embed-ready) + per-family entry counts
python3 indexer/mind_index.py stats
```

Run from this skill's directory, or pass `--db` if the index moved.
`--json` reports which tier answered (`"mode"`: command | fts |
vector), so you can tell which lane answered and detect degradation
explicitly.

**Query craft.** Search the *intent*, not the command you guess:
"make a subject pop from a blurred background" beats "focus". If you
already know the id, search it verbatim for the full card. If the
first query misses, rephrase with the intent's noun and verb before
assuming the tool is absent. Verify a resolved command's params and
traps with a follow-up exact-id search before writing it into a plan.

**Degradation ladder — every state is usable:**

| Situation | Meaning | Action |
|---|---|---|
| DB absent or empty | index not shipped or corrupt | Read or grep `references/mindmaps/<family>.md`; do NOT attempt `rebuild` — slice files are build-fleet artifacts, not shipped |
| No config at `~/.photocraft-art-director/config.json`, or it is unreadable | keyword-only mode, by design | Proceed — tiers 1–2 answer most art queries; query with concrete terms; never retry the endpoint mid-task |
| Embed endpoint down or flaky | command + FTS already ran; they are local and unaffected | Rephrase the query as a command id or concrete keyword (forces tiers 1–2), or read the family md |
| Search returns no rows | phrasing miss, or the tool is genuinely absent | Widen → grep the mind maps → rephrase the intent as the visual goal; only then conclude the tool is absent |
| Host has no Python | CLI unusable | The 16 md files are the full browse floor; they cover every family |

Pick the mind-map family by domain: blur → `filter-blur`; other
filters → `filter-other`; painting/brushes → `paint`;
selections/transforms → `edit-selection`; layers/styles → `layer`;
masks/channels → `mask`; gradients/fills → `gradient-fill`;
shapes/paths → `shape-path`; adjustments → `adjust-image`; smart
objects → `smart-objects`; text → `text-type`; documents/files →
`doc-file-app`; session/inspection → `session-jobs`; MCP/CLI surface
→ `mcp-surface`; UI/bridge → `ui-bridge`; config/presets →
`system-config`. Every entry carries a "choose it when…" one-liner;
the index card adds params and traps.

**Secrets discipline.** The runtime config at
`~/.photocraft-art-director/config.json` (when present) carries the
embedding endpoint credentials; it lives outside any skill tree and
repo, and its contents are never printed or copied into any file. Only
the fact of its presence and the observable `mode` behavior matter.
Configure it locally from `indexer/config.example.json` when semantic
search is wanted.

`rebuild` and `export` are maintainer operations that regenerate the
index and the mind maps — never run them mid-task (`export` overwrites
the family files whole).

## Reference files

| File | Holds | Open when |
|---|---|---|
| `references/grammar.md` | Subject→grammar fit table, register coherence, focal hierarchy, depth ladders, frame closure | Drafting the charter's grammar section; any shape/rhythm/composition finding |
| `references/palette-light.md` | Derivation recipes, light-source tracing, blend-mode physics, gradient construction, accent discipline | Choosing palette relations; any light-logic finding |
| `references/failure-classes.md` | Named defect classes: detection cue, repair rule, fix tier, prevention | Phase 1 import; before choosing any fix |
| `references/acceptance.md` | Budget templates per element type, probe patterns, visibility bar, adjudication flow, certification law | Writing budgets; every audit-response decision |
| `references/intent-to-tools.md` | Intent→family routing table; field-proven command chains for recurring intents, with acceptance probes | Phase 4 build; when an element needs a proven recipe |
| `references/mindmaps/*.md` | Generated per-family command one-liners | Search-index fallback (degradation ladder) |

## The loop in one line per phase

Charter before strokes; grammar fitted to subject; palette derived
from light; build to a budget; classify then fix in place; probe
every claim; certify and stop.
