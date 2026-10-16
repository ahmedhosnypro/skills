# pptx-engine — pptxgenjs engine law beyond building.md's pitfall list

Read when the original has a real bullet list, a native-styled chart,
shadows, merged table cells, or speaker notes. Two defect classes in here
share one asymmetry that matters to this pipeline: **LibreOffice renders
them fine while PowerPoint repairs/garbles the file** — the LO render gate
and PIL checks are structurally blind to them, so they are law, not advice.

## Native bullets

pptxgenjs has native bullets; `bullet` is a **per-paragraph** property — it
goes inside the rich-text item's own `options`, not only on the box.

- Glyph: `bullet: true` (round) or `bullet: { code: "2022" }`. Common codes:
  `2022` (•), `25AA` (▪), `2013` (–), `25B8` (▸). Match the original's glyph
  by measuring it, not by habit.
- `indent: 10`–`16` closes the hanging gap — without it the glyph floats
  visibly detached from the text. Measure the original's hang and pin it.
- **Never put the bullet glyph in the text**: `text: "• item"` (or
  `unicode: "•"`) combined with `bullet: true` renders DOUBLE bullets.
- Manual `"• "` prefixes are still the right tool for pinned-pitch boxes
  (the explicit-line-spacing pattern): manual keeps the glyph on the
  measured pixel with full per-line control. Use native bullets when the
  original is a genuine hanging-indent list with uniform indentation.

## Rich-text paragraphs — the pPr trap LO never catches

When several runs share ONE paragraph (runs without `breakLine` between
them), each run's paragraph-level options make pptxgenjs emit its own
`<a:pPr>` inside a single `<a:p>` — schema-invalid XML. PowerPoint garbles
the text or prompts repair; **LibreOffice renders it normally**, so the
render gate, the closed-loop PIL checks, and the judge leg all pass a
corrupt deck.

- End every paragraph with `breakLine: true` on its last run.
- Paragraph-level options (`align`, `bullet`, `lineSpacing`, `paraSpaceAfter`)
  belong on the FIRST run of the paragraph only; mid-paragraph runs carry
  character-level options (`fontSize`, `color`, `bold`) alone.
- One paragraph = one run unless a measured mid-line style change forces
  more; if more, re-read the emitted XML before trusting the LO render.

## Option objects are mutated — use factories

pptxgenjs stamps internal state into the option objects you pass (bullet,
shadow, and shape options especially). A shared `const OPTS = {...}` reused
across elements comes back polluted and corrupts every later use.

- Wrap per-element options in a factory function returning a fresh object
  per call; never share option literals across addText/addShape/addImage.
- Applies to the bullet `{ code, indent }` objects above and the shadow
  objects below.

## Shadows

```js
options: { shadow: { type: "outer", color: "000000", offset: 3,
                     angle: 90, opacity: 0.4, blur: 3 } }
```

- `color` takes 6-char hex with NO `#` — the same hex law as everywhere
  else in pptxgenjs.
- `offset` must be **non-negative**; negative offsets render as artifacts.
- `opacity` is 0–1 — not a percentage, not hex transparency.
- `angle` is degrees (0–359), the direction the shadow falls.
- LO drifts on shadows (softer edge, shifted angle) vs PowerPoint: when the
  original's shadow is a fidelity-critical feature, PIL-check the shadow
  band on the LO render but accept PowerPoint-side variance as unmeasured.

## Native charts (addChart)

- Legitimate ONLY for simple native-styled charts in the original (plain
  bar/line/pie with stock axis and label styling). graphs.md's
  generated-image law still governs scientific plots (scatters, decision
  regions, model-output curves) and is NOT superseded by anything here.
- **Trap: `dLblPos: "outEnd"` is invalid under `barGrouping: "stacked"`** —
  the file triggers a PowerPoint repair prompt while LO ignores the value
  and renders fine (same blind-spot asymmetry as the pPr trap). Under
  stacked grouping use `"ctr"`/`"inEnd"` or omit `dLblPos` entirely.
- Chart data goes in typed arrays (`labels`, plain value arrays per series);
  series/axis/label colors take 6-char hex without `#`.
- A native chart is certified the same way as any element: PIL-measure the
  original's plot box and closed-loop-verify the chart's rendered frame
  before the judge leg. If the original's chart is pixel-dense or
  hand-styled, fall back to shapes or a generated image — a native chart
  that only approximates the original is not a fidelity win.

## Tables — merged cells

- Cell options accept `colspan`/`rowspan`: build the table as a grid, put
  the span value on the anchor cell, and omit the covered cells entirely.
- The LO row-floor law (building.md) applies to every rendered row,
  including merged ones.

## Speaker notes

- `slide.addNotes("...")` attaches a note; notes never render on the slide
  surface, so they are not a fidelity surface and cannot affect the judge
  leg either way.
- Add notes only from owner-supplied content (transcript text, provided
  notes); never invent them — the never-invent law applies verbatim.

## Slide masters — deliberately not used

`defineSlideMaster` exists for authoring reuse; recreation does not use it.
House chrome is drawn explicitly per slide (patterns/house-chrome) because
per-element placement is exactly what the closed-loop PIL checks certify.
Moving chrome onto a master takes it out of the build script, where pixel
law can no longer reach it — never refactor a certified build onto a slide
master.
