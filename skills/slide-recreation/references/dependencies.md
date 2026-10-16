# Dependencies — dependent-slide build gating & shared component builds

Binding law for ANY deck whose advanced slides re-use a previous slide's
composition — same video or not. First proven on a 45-slide deck with a dense
dependency web; later extended with CROSS-DECK edges and PATTERN GROUPS.

## What a dependency is

A dependent slide ("child") is its parent's composition **plus a delta**: extra
blocks, removed blocks, or blocks replaced by different ones. The owner
supplies the graph — curation of what depends on what is human-owned, like the
frame set itself. Edges are direct-parent (child → the slide it builds on);
chains compose transitively (30 ← 29 ← 26 means 30's composition contains 26's
via 29).

## What a dependency is NOT

- A **pattern group** is NOT a dependency: members share reusable patterns
  (e.g. the same diagram family), not identical compositions. Pattern groups
  build STRICTLY sequentially (verify the pattern, then reuse it) but imply no
  component import and no content identity.
- A family-level pattern-library entry (house chrome etc.) is shared chrome,
  not a slide dependency.

## Canonical storage

- `<video>/slide_dependencies.json` — the owner's edge list (source of truth).
  v1 (same-deck only):

  ```json
  {"edges": {"7": [6], "8": [6], "30": [29]},
   "shared_image_sources": {"14": ["slide_18_source/"]}}
  ```

  v2 adds qualified cross-deck parent refs and pattern groups:

  ```json
  {"edges": {"4": ["<course>/<video-A>:15", "<course>/<video-A>:18"],
             "10": [9]},
   "pattern_groups": {"P1": [9, 10, 12, 14, 16]},
   "special": {"57": "encoder+decoder composition rule"},
   "shared_image_sources": {"51": ["<video-A>/slide_18_source/"]}}
  ```

- Progress DB: `depends_on` column (csv of parent tokens, `''`/NULL = root)
  plus `pattern_group`/`pattern_seq`. Token grammar: bare int = same-deck
  parent; `<course>/<video>:<slide_id>` = cross-deck parent. The progress-DB
  helper applies edges and groups automatically at registration; its
  dependency view prints per-slide `root | blocked | unblocked` with what each
  blocked slide is waiting on; the buildable query prints the exact dispatch
  list (content gate + dep gate + pattern gate + not-yet-built).

## The gate (what is blocked and what is not)

- **Analysis and validation are NEVER blocked** — by dependencies OR pattern
  groups. Every slide, dependent or not, can be analyzed and validated in
  parallel.
- **BUILDS are gated**: a dependent slide's build may start ONLY when every
  dependency is **certified** — generated-status passed AND visual_check PASS.
  Cross-deck parents certify in THEIR OWN deck's DB (resolve them read-only
  across namespaces — never write outside your deck). Before dispatching or
  starting a build, run the dependency view; if your slide shows `blocked`, do
  NOT build (report and stop — the orchestrator re-dispatches when the parent
  lands). A builder that verifies the canonical graph before building
  (refusing on DEP_BLOCKED) is the correct behavior even when the
  coordinator's brief said otherwise.
- **Siblings unblock together**: one parent's certification unblocks ALL its
  children at once (slide 6 certifying unblocks 7, 8, 9, 10 simultaneously —
  dispatch them in parallel). Cross-deck certification cascades the same way
  across namespaces.
- **Pattern groups gate sequentially**: member k waits for member k−1's
  certification, in the owner's listed order. Dispatchers must NOT fan a whole
  group out in parallel.

## Shared component builds (the "u-components" model)

Child builds MUST import the parent's certified composition as a shared module
— **never copy-paste it, never re-derive its geometry**:

```
<video>/recreated_pptx/build/
  components/                    # shared, importable, certified building blocks
    house_chrome.js              # primitives: frame + badge + title (house rule)
    slide_006.js                 # a parent slide's FULL certified composition,
    ...                          #   exporting e.g. renderBase(pptx, slide, opts)
  slide_007.js                   # child build: require('./components/slide_006'),
  slide_008.js                   #   call the parent render, then apply the delta
```

- A child build = `require` the parent component → render base → draw ONLY
  the child's own delta (its extra/replaced blocks, at the child's measured
  geometry).
- **Deltas can REMOVE or REPLACE parent blocks** (measured on a real deck: 6
  of 15 children drop or replace inherited blocks; only the rest are pure
  supersets). So export the parent at BLOCK granularity: one function per
  visual block (e.g. `drawContextVectorCallout(slide)`) plus a convenience
  `renderBase(pptx, slide, opts)` that draws them all, optionally with
  `opts.skip`/`opts.only` selectors. A child composes selectively per-block —
  NEVER draws the full base and tries to erase. The child's own frame is
  ground truth for what survives, moves, or changes.
- **SKIP-CHAIN composition**: when a descendant needs to skip a block the
  parent's API doesn't offer, compose the chain from the components' EXPORTED
  per-block functions at the owning level (chrome → grandparent blocks minus
  title → deltas → deltas), skipping selectively where each component exports
  its blocks — never re-derive geometry, never import a monolith. Document
  the skip chain in the build header.
- **Fork-vs-inherit is decided by a full-grid pixel diff, not by a banked
  claim.** Before forking a parent's mechanism as a "re-style", run the cheap
  full-grid diff between the two frames (tol-bucketed identical-fraction +
  per-cell maps): same chrome + >50% identical pixels means INHERITANCE
  (renderBase + delta zones — measured 70.16% identical on a pair a banked
  verdict had called a "full re-style", costing a day of work); a frame
  sharing ONLY outer margins with its parent justifies a fork. A child whose
  frame shares only margins may skip the parent's block calls, but MUST
  document the frame-diff evidence in its banked component header — children
  of children read that header to know what they inherit.
- Components are **certified single-source-of-truth artifacts**: once the
  parent is judge-certified, its component is frozen. Copy-then-modify; never
  overwrite a certified component in place.
- **Cascade law**: editing a certified component re-opens EVERY descendant —
  rebuild and re-judge the whole subtree, or (better) leave the component
  alone and express the change in the child's delta.
- Chains compose naturally: slide 30's build imports slide 29's component,
  which itself imports slide 26's — the composition is the import graph.
- **Cross-deck children** (v2) import the parent deck's component by ABSOLUTE
  path (`require(<absolute path to the parent deck's
  build/components/slide_NNN.js>)`). Identical recap slides are typically
  `parent.renderBase(...)` + the child's own badge numeral + a tiny measured
  delta. The multi-deck isolation rule is intact: the child READS the
  parent's banked artifacts; it never writes into the parent's namespace.
- **Family-scoped banking obligation** (v2): bank a component at certification
  when ANY slide in ANY deck's graph references you — even with no same-deck
  dependents (precedent: three slides were childless in their own deck but
  parents for the next one). A certified slide without a needed component
  must be retro-banked additively (derive the per-block module from its build
  script, verify 0-pixel-diff against the certified render, never touch the
  certified pptx).

## Cascade execution laws (re-certification lanes)

- **A defect register's (CASCADE_DELTA / DEFECTS) measured parameters are a
  guide, not ground truth**: re-derive each item from the frame before
  executing — registers have prescribed wrong radii and wrong fill/ink roles
  (an "asterisk" that is a solid blob; "faint lines" invisible to the
  prescribed mask). Where register/spec text and frame disagree, the frame
  wins and the deviation is documented in the build header.
- **Cascade pixel gates need masks covering the slide-local deltas' FULL
  extents** — parent-only ink the delta replaces, draw-order seams (a
  slide-local block redrawn AFTER renderBase inverts occlusion wherever it
  overlaps an inherited block — mask the seam explicitly), and the child's
  own redrawn geometry. Connected-component the diff and attribute every
  cluster to a draw-call line number; otherwise the "0 px" gate is
  unfalsifiable noise.
- **Inherited render artifacts are erased child-locally**, never patched in
  the frozen parent: cover the band + repaint the underlying cells at exact
  parent geometry, sampling every layer the band covers (above-border fills
  included) or the eraser leaves a visible seam. The parent's other children
  and its own certification stay byte-stable.
- **"Rebuild-unchanged" cascade verdicts: never use deliverable md5** —
  pptxgenjs embeds a fresh creation timestamp in docProps/core.xml on every
  build, so two builds of the byte-identical script always differ. Compare
  zips part-by-part (hash every namelist member; the only differing part was
  docProps/core.xml → content-identical). Keep a pre-rebuild backup of the
  deliverable so certified bytes can be restored either way.

## QA implications for dependent slides

- The child's **closed-loop PIL self-check covers its delta regions**;
  inherited regions are re-verified cheaply (they should be pixel-comparable
  to the parent's certified render — same component, same draw) but the
  mandatory checks still run on the full slide (containment, wrap, etc. apply
  to everything the child draws).
- Judge dispatch: keep the frozen `-p` template VERBATIM; carry the
  shared-base fact in the worker-editable `--view` context, e.g. "the base
  composition is slide 6's judge-certified component (imported, not
  re-drawn); the expected difference is exactly this slide's delta". A judge
  finding about an inherited region is handled like the inheritance law: if
  the pixels are identical to the certified parent's, the finding is judge
  variance (document, override) — unless the CHILD's own draw broke the
  region, which is a real fix trigger. (Full adjudication rules: judging.md
  inheritance/cascade law.)
- House chrome is drawn ONCE in the component (or the shared primitive) —
  children must not re-draw it on top.

## Onboarding a new dependent deck

1. The owner curates the frame set (HARD STOP gate) and supplies the edge list
   (in-deck edges, cross-deck qualified edges, pattern groups, special
   notes).
2. Machine writes `slide_dependencies.json`, reconciles index/mapping
   (`new2old_mapping.json`, rewritten `slides_index.json`, old index + DB
   preserved as evidence), and the DB seeds rows WITH edges and groups.
   Placeholder covers (missing frames) get a placeholder analysis status and
   skip analysis/validation entirely; they certify by owner sign-off + chrome
   check (a judge comparison is impossible without a ground-truth frame).
3. Analysis/validation fan out over ALL slides; build dispatch fans out only
   over the buildable query's output, in waves driven by certification events
   (including cross-deck parents certifying in their own deck's waves);
   pattern groups dispatch one member at a time in listed order.
