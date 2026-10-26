# Equations — professional 2D format, alignment law, OMML dual-representation

Binding rule: any equation on a recreated slide is rendered in **Professional
Format (2D / non-linear)** — never linear/typed notation:

- **Fractions**: stacked with a horizontal fraction bar — never inline `a/b`.
- **Summation `∑`**: large glyph with limits placed the way the ORIGINAL places
  them (above/below `undOvr` or stacked to the right `subSup` — sibling slides
  in one deck differed) — never `sum from i=1 to n`.
- **Sub/superscripts**: spatially aligned with math-font spacing — never
  `x^2`/`x_1` text or Unicode look-alike approximations.

The equation's CONTENT stays verbatim from the spec; only the rendering is 2D.

## Certified mechanism: matplotlib mathtext → PNG → addImage

1. Render: `python3 scripts/render_eq.py '<mathtext>' <out.png> <fontsize_pt>
   '<#hex>'` (skill-local certified copies: `render_eq.py` base;
   `render_eq_wide.py` overlap-guarded variant for wide equations;
   `render_eq_stix.py` STIX-serif variant) — 600 dpi, tight bbox, transparent
   background; prints a JSON sidecar with exact pixel w/h and `baseline_frac`.
   **The color argument REQUIRES the `#` prefix** (`'#C00000'`): matplotlib
   parses a bare 6-hex string starting with a valid cycle id (`C0`, `C1`...) as
   that CYCLE COLOR — silently blue instead of an error. (Inverse of pptxgenjs,
   which forbids `#` — building.md.) PIL-probe every generated PNG's dominant
   ink color after generation (`np.where(alpha>100)` dominant RGB) — a
   default-blue equation PASSED a full-slide judge; the dense-region crop
   comparison and the asset probe are what catch it.
2. Embed at EXACT size: `w = px/600` inches, `h = py/600` — NEVER rescale
   (blurs glyphs). Size and color are baked at render time.
3. PNG only (never SVG). Mathtext is a LaTeX subset; DejaVu math look is
   acceptable (vision-validated). STIX serif when matching a serif original.
4. Bank every generated PNG + sidecar (e.g. `build/assets/eq_NNN_*.png/json`);
   never delete them.
5. **Record the EXACT final mathtext string, never prose, the moment you accept
   it** — a tuned `\;`/`\quad` spacing fix described as "tuned \qquad" forced
   ink-cluster forensics to recover the strings. The sidecar's `mathtext` field
   (or the slide's math report) is the provenance record the OMML pass and any
   rebuild consume.

### render_eq failure modes (measured)

- **Wide expressions (>~7in ink) get their LEFT edge silently clipped** — the
  baseline probe collides with the left tail. Use the wide variant, and always
  PIL-measure ink edges rather than trusting the tight bbox.
- **`\frac` renders operands at SCRIPT size** (~10pt on a 14pt line, stack
  compressed to 24.7pt) — full-size stacked operands need `\dfrac` (+ serif
  when the original is serif) re-rendered at the size matching the original's
  measured stack height.
- **`\dfrac` vs `\frac` changes the PNG size at the same fontsize** — when
  regenerating a certified asset, match the sidecar dims exactly or the embed
  gets rescaled (a law violation).
- **Color defects are per-slide facts.** Before touching a CERTIFIED slide on a
  color suspicion, PIL-census the ORIGINAL frame's saturated ink and compare
  against the build's asset census — matching mixed palettes (blue + red
  equations) = correct; only a real mismatch is a fix trigger.

## EQUATION ALIGNMENT LAW (owner feedback — overrides a judge PASS)

Placement defects (horizontal/vertical) are fix triggers EVEN WHEN THE JUDGE
PASSED. Original geometry wins; the recreation adapts (shrink/shift the bullet
column if needed — but verify a collision actually exists before deviating: one
worker shifted equations +73px right "to avoid collision" that PIL measurement
proved nonexistent).

- **Vertical**: put the image's math BASELINE on the text baseline:
  `y_image = target_baseline_in − baseline_frac × h_image_in`.
  "Center the image on the line" (`lineY − h/2`) is WRONG for anything taller
  than the line.
- **Horizontal**: PIL-measure the equation's ink LEFT EDGE in the original frame
  (1px = 1pt) and match it, accounting for the PNG's tight-bbox inset (~8px at
  600dpi). Beware font-width differences: DejaVu is wider than some originals,
  shifting the bar position inside a boxed equation — re-render, don't just
  nudge.
- **Closed-loop verification (mandatory before judging)**: render, then
  PIL-compare the equation's ink band in the 150dpi render against the
  original's measured region (scale ×2000/960): top/bottom/left/right ink edges
  within ~4px. Iterate placement until within tolerance. Residual glyph-metric
  differences (a mathtext superscript sitting ~2pt higher, a radical descending
  less) are inherent — document them, don't chase them by breaking the baseline
  law.
- Single-line caption/label baselines under pinned lineSpacing land ~1.5px off
  any descent-formula prediction — place empirically: measure render, nudge
  box y, re-render (validated to 0.7px).

## DELIMITER DIRECTION LAW (paren mirroring — overrides a judge PASS)

A delimiter pair is two DISTINCT mirrored forms. Anatomy of a real glyph: "("
has its cusps (stroke ends) at the INNER side — pointing right, toward the
enclosed content — and its belly (extreme ink) at the OUTER left; ")" mirrors
it (cusps inner-left, belly outer right). The openings face each other.

- **FORBIDDEN — one bow-direction template reused for both sides with only an
  x-offset.** Both sides then render the same shape (measured on certified
  decks: a vector box whose two parens both bowed right — the left one
  mirrored). The defect ships silently through full-slide judges at hairline
  stroke widths; only a zoomed crop comparison or the closed-loop check
  catches it. Hand-drawn arcs (frame-matched reconstruction) must author EACH
  SIDE as its own template: left = endpoints at the INNER x, belly control at
  the OUTER x; right = the mirror. Never one `verts` list for both.
- **FORBIDDEN — "fixing" direction by vertical flip** (a paren is vertically
  symmetric: flipping "(" vertically still yields "(") **or by horizontal flip
  of a font glyph** (stroke weight/contrast no longer matches the mechanism's
  other glyphs).
- **Preferred: real glyphs from ONE mathtext expression** (`$\left(...\right)$
  or plain `(...)` in the expression) — correct by construction. Delimiters
  from mathtext PNGs, stretched-glyph crops of real glyphs, native OMML/font
  glyphs, or the arc pattern's per-side `angleRange` are direction-correct by
  construction; hand-drawn Beziers are where this defect lives.
- **Closed-loop direction check (mandatory before judging; a judge PASS never
  waives it)**: middle-band extremum test — in the middle third of the
  delimiter's ink-row span (excluding horizontal-bar rows such as `=` bars),
  "(" has its extreme ink on the LEFT of its full span, ")" on the RIGHT.
  Run per delimiter on the generated asset, on the matching crop of the 150dpi
  render, and on the original-frame crop (ground truth). Mirrored = defect =
  rebuild the asset. Checker: `references/patterns/delimiters-direction-check/
  check_paren_direction.py` (auto-pairing or explicit `--expect` windows;
  exit 1 on any mirrored or unresolved stroke).

## OMML dual-representation (post-certification pass)

Raw OMML in a PPTX does NOT render in LibreOffice headless (it shows the linear
fallback — measured; OnlyOffice/Aspose/Gotenberg are no better). The validated
solution keeps the certified PNG pixels and adds editable PowerPoint equations:
wrap each equation `<p:pic>` in `mc:AlternateContent` — `mc:Choice
Requires="a14"` holds real OMML, `mc:Fallback` holds the original PNG pic
verbatim (pattern omml-wrap: `example.sh` documents the workflow,
`skeleton.xml` shows the authored structure; a zip-level post-processor that
touches no rels/content-types implements it).

- **The Choice must carry the PowerPoint-AUTHORED pattern** — the naive
  LibreOffice-writer pattern (`a:p > a14:m > bare m:oMath`) makes PowerPoint
  honor the Choice and render NOTHING (equations invisible — measured). The
  working pattern emits `a:pPr(algn=ctr+buNone) + a14:m >
  m:oMathPara(jc=centerGroup) > m:oMath + endParaRPr`, Cambria Math typeface +
  `i`/`smtClean="0"` on every run, `m:ctrlPr` in every construct, Choice shape
  id = the Fallback pic's id, zero-inset `bodyPr anchor=ctr noAutofit` pinned
  to the pic frame. The authoring oracle for ANY PowerPoint-only feature (MCE
  Choices, a14, OMML) is a REAL PowerPoint-authored file — never LO's writer,
  never LLM-synthesized markup (web answers confidently fabricate MathML tags;
  decks that merely LOOK promising often carry PNG equations). Test matrix
  exercises BOTH MCE branches: the Fallback leg via 0-px-diff LO render, the
  Choice leg via a parse/well-formedness proof of a Fallback-stripped copy.
- LibreOffice render of the wrapped file is pixel-identical (validated 0 of
  2.25M px per wrapped slide); PowerPoint shows editable native equations. No
  re-judge needed.
- Manifest per slide: `{"slides":[{"slide":1,"equations":[{"rel_id":"rId1",
  "image":"eq.png","mathtext":"...","font_size_pt":22.0,"color":"#C00000"}]}]}`
  — values come straight from the render sidecars; `rel_id` is RE-DERIVED from
  the actual pptx rels after any rebuild (never assume it survives).
- **Multi-embedded assets: one manifest entry per embed with explicit
  rel_ids.** When one media file serves several `<p:pic>` rel ids, basename
  matching fails loudly and the descr fallback resolves only the first pic —
  inventory the rel ids first.
- **A plain slide embedding a byte-identical copy of another slide's certified
  equation asset inherits that asset's proven manifest values**: prove identity
  by md5 of the embedded media vs the banked asset + embed-box geometry
  (px/600), never by re-rendering the PNG. A "no size match" in a font-size
  provenance scan can be a `\frac`-vs-`\dfrac` probe artifact, not a
  provenance failure — the OMML is generated from the mathtext string, never
  by re-rendering the PNG.
- Rules: apply ONLY after visual certification; apply to the slide's own pptx
  (the single plain-named deliverable — no `_omml.pptx` variants per the
  single-version law); verify 0-pixel-diff before accepting; **never
  LibreOffice-resave a wrapped deck** (the LO writer drops OMML it never
  understood).
- **Mathtext provenance**: sidecars don't always carry the mathtext string —
  take it from the slide's math report (or the sidecar if recorded there),
  then RE-RENDER it with the slide's exact helper (wide/STIX variants included)
  and PIL-verify 0 pixel diff vs the banked PNG before wrapping (the OMML must
  provably match the fallback image). Trust the sidecar's font size over
  estimates (sidecar 20.0pt vs ~21.7pt estimated).
- The converter supports m:f, m:rad, m:nary (∑∏∫; `undOvr` or right-stacked
  `subSup` limits — select by the ORIGINAL's placement, per the mathtext
  idiom: `\sum{}_{m=1}^{D}` → subSup; plain `\sum_{}^{}` → undOvr),
  m:sSub/sSup/sSubSup, m:bar, m:acc, m:d, Greek + operators, `\text`,
  `\mathbb{}` (double-struck ℝ/𝕀), `\dfrac`/`\tfrac`, `\Vert`, `\mathbf`,
  `\vdots`, the `x{}_1` empty-group idiom; anything else fails loud — never
  hand-patch OMML.

## Renderer verdicts (researched, don't re-derive)

No better headless Linux PPTX renderer exists than LibreOffice: OnlyOffice
drops OMML and is HTTP-only; WPS/Calligra have no headless CLI; Gotenberg is
LO-in-Docker; Aspose watermarks, is costly, and renders the image fallback
anyway; PowerPoint COM is Windows-only. A LibreOffice extension cannot fix
equation rendering for headless convert-to-pdf. LO itself saves equations as
the same AlternateContent pattern the wrapper emits — which is why the wrapper
mirrors it.
