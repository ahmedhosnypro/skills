# mermaid.js parity defect suite

**What this proves:** every diagram under `defects/` is one that the
reference renderer (mermaid.js — the engine behind GitHub issues, pull
requests, READMEs, GitLab, and the live editor) rejects as a parse error,
and therefore renders as a broken diagram on GitHub.

Each file in `defects/` is minimal, includes a `%%` header naming the
construct and the reference parser's rejection, and MUST be detected as
invalid by at least one available renderer. The suite exists because the
offline structural validator alone does not catch any of these — all six
files in this directory, the five defects and the one legal control, pass
gate 1.

Run it with:

```sh
cd skills/mermaid-diagrams && bun test ./tests/mermaidjs-parity/parity.test.ts
```

## What is checked

| Fixture | Defect | Reference parser result |
|---|---|---|
| `defects/sankey-beta-title-line.mmd` | sankey has no `title` statement | `Parse error on line 2` |
| `defects/xychart-y-axis-worded-range.mmd` | y-axis bounds need `-->`, not a word | `Parse error on line 4` |
| `defects/xychart-y-axis-empty.mmd` | y-axis needs a label, a range, or both | parse error |
| `defects/requirement-diagram-hyphenated-id.mmd` | attribute values are identifier tokens | `Parse error on line 3` |
| `defects/requirement-diagram-inline-body.mmd` | attributes must each be on their own line | `Parse error on line 2` |

`defects/radar-beta-bracket-label.mmd` is a **legal control**, not a
defect: mermaid.js parses `curve id[Display label] {…}` and renders the
label. It is included so this suite cannot "pass" by rejecting everything.

## Renderers

Every fixture is rendered by **both** renderers — `mmdr` (gate 2) and
`mmdc` (gate 3) — and each fixture gets one test per renderer, so a
renderer that is missing or broken shows up as `unavailable` instead of
silently vanishing. The three assertion tiers:

1. **Gate 2 — `mmdr`:** the renderer was exercised. Accepting a defect is a
   *valid, expected* outcome: it is exactly the leniency these fixtures
   exist to document, so an acceptance is recorded, not failed.
2. **Gate 3 — `mmdc`:** the reference renderer rejects every defect. This
   is the assertion with teeth, because mermaid.js is the engine GitHub,
   GitLab and the editors run — it is the authority on whether a diagram
   publishes.
3. **Doctrine:** each defect is detected by at least one *functional*
   renderer (one proven able to draw the legal control), so a broken
   launcher cannot fake detection by "rejecting" everything.

Because the released `mmdr` build accepts several of these constructs, it
is normal for a defect to be rejected only by gate 3 — and the per-fixture
per-renderer tests make that split visible on every run. Once the upstream
fix merges, the gate-2 column starts showing rejections too; no test needs
to change either way.

## Known divergence

`mmdr` renders the radar control with its raw `id[label]` token leaking
into the legend instead of the display label. That is a visual defect in
`mmdr`, not a parse defect, so it does not fail this suite; it is reported
as a warning. A fix is submitted upstream in
[mermaid-rs-renderer#165](https://github.com/1jehuang/mermaid-rs-renderer/pull/165).
