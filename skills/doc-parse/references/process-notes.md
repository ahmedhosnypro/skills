# doc-parse — lane-facing process notes

Operational doctrine, defect vocabulary, and adjudication rules for
parse lanes. The audit-prompt contract is the script's own output
shape; this file is the append-only knowledge base. The script and the
config are frozen — script change proposals go to the "Script
proposals" section at the end of this file.

## Adjudication law

- **The source image is the ground truth.** Every banked claim about
  the parse (or about the document) is checked against the image —
  via a vision subagent when the claim is visual — and classified
  REAL / HALLUCINATED / DEBATABLE with measurements. Coordinate tokens
  (`<x_…>`, `<y_…>`) are content-normalized (0..1; x by width, y by
  height) and resolve to pixel boxes; class tokens resolve to layout
  roles. A bounding box that lands on empty canvas is measured, not
  assumed.
- **A blank parse of a text-bearing image is a FAIL**, never a
  "no result": `content` empty, or content with no text and no
  coordinate/class tokens, on an image that visibly carries text.
- **The standard is LOOKS WRONG = flag, not source-correct = pass.**
  A correct string behind a mangled reading order is still a defect.
- **Never bank a claim as a defect when two reads contradict** —
  advisory at most. Corroborate with a second read: a re-parse at a
  different `--max-output-tokens`, or a vision-subagent cross-check of
  the one question in doubt.
- **Label every verdict `single-read` vs `corroborated`** in the
  register. Never phrase a single read as a consensus.
- **Definiteness and pass/fail are separate questions.** A degenerate
  input (zero-byte file, integrity-check failure, wrong file re-used
  from a stale export) is NO-RESULT — re-probable, out of every done
  counter, never a verdict.

## Defect vocabulary (append-only; dedup first, near-duplicates become "confirms <tag>")

- `reading-order-inversion` — text present but sequenced against the
  visual order (columns read before headers, footnotes mid-paragraph).
- `table-structure-loss` — a visible table parsed as flat text (no
  markdown table shape, columns collapsed, header row merged).
- `hallucinated-content` — text in the parse with no counterpart in
  the image (measured: token box on empty canvas, or string absent
  from the image's visible text).
- `dropped-region` — a visible region (chart, sidebar, caption, stamp)
  with no parse coverage at all.
- `coordinate-misalignment` — `<x_/y_>` boxes landing on the wrong
  content when resolved against the image dimensions.
- `class-token-mismatch` — a `<class_…>` label contradicting the
  region's actual role (a `<class_Chart>` over a table, a
  `<class_Section-header>` over body text).
- `chart-token-pollution` — chart-internal text leaking unstructured
  into the flow (the `<class_Chart>` handling failed) instead of being
  chart-contained.
- `multilingual-script-errors` — CER-style garbling on non-Latin
  scripts (the model card's MOSCAR/IndicVision coverage is the
  expectation baseline: Latin, Arabic, Cyrillic, Han, Hangul, Japanese,
  Indic, Hebrew, Thai, Greek).
- `resolution-degradation` — quality loss attributable to an oversized
  input (past the 1664×2048 recommendation) rather than the model.
- `math-normalization-loss` — formulas flattened where the upstream's
  postprocessing promises LaTeX/markdown conversion.
- `options-ignored` — `decoding.max_output_tokens` truncation not
  honored (mid-token cut) or silently exceeding the ask.

## Operational notes

- Latency runs ~15–40 s per page (measured on the slide-JPEG reference
  corpus); a batch of N pages is a background job, not a foreground
  drip.
- The endpoint's JSON body passes the family's response through
  verbatim (`content` + `usage`) — transport parity against a second
  configured endpoint is a valid corroboration read for transport, not
  for model quality.
- `usage.output_tokens` is the only usage field the family reports;
  input tokens are absent — do not infer them.
- Config rotation: replace the config's field VALUES in place, never
  rename the file; the script resolves it relative to its own
  location.

## Script proposals

Proposed changes to `scripts/parse_document.py`, evidence-motivated.
NEVER applied by an agent, lane, or session — only the human owner
applies and records them, with a frontmatter `version` bump. The
script is frozen for everyone.

(empty — no proposals yet)
