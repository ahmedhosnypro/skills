// Pattern: explicit-line-spacing
// PowerPoint and LibreOffice pick DIFFERENT automatic line pitches for the same
// font size; over a tall multi-line block the drift pushes the last line past
// bounds that LO verifies as fitting. Pin the pitch explicitly on EVERY
// multi-line text box so both renderers agree and the LO check predicts PowerPoint.
// Run:  NODE_PATH=$(npm root -g) node example.js   -> demo_line-spacing.pptx
//
// LAWS:
// - EVERY multi-line text box sets explicit `lineSpacing: <pt>` (pptxgenjs ->
//   a:lnSpc > a:spcPts, honored identically by both renderers). Never rely on
//   auto pitch near frame bounds.
// - Prefer a SINGLE knob: drop `paraSpaceAfter` and pin the FULL pitch on
//   lineSpacing so the rendered band pitch == the pinned value exactly.
// - Two pin variants, choose deliberately:
//   (a) COMPLIANCE PIN (current layout already certified): measure the render's
//       current band pitch and pin EXACTLY that -> render stays pixel-identical
//       and the existing certification carries at zero vision cost. Do NOT
//       "improve" the pitch during a compliance pin (moves certified ink).
//   (b) DEFECT-FIX PIN (slide re-opened for a defect, re-judge mandatory anyway):
//       pin to the ORIGINAL's measured band pitch, not LO's auto pitch.
// - Blocks near a frame bottom keep >= 0.4in bottom clearance in the LO render.
// - EMPTY-RUN PITFALL: pptxgenjs empty text runs ("") DROP their fontSize — the
//   XML gets a default-size endParaRPr and the "blank line" renders one band
//   tall, overflowing anchored boxes on BOTH edges. Use single-SPACE runs (" ")
//   at an explicit small size for spacer lines.
// - Verify post-build: re-measure the render's band pitch == pinned value, and
//   assert `a:lnSpc > a:spcPts` entries in the slide XML.

const pptxgen = require("pptxgenjs");

// ---- parameters -------------------------------------------------------------
const PITCH = 24;        // pt — the pinned line pitch (from measurement; see laws)
const LINES = ["line one of a tall block", "line two of a tall block",
               "line three of a tall block", "line four of a tall block"];

// ---- build -------------------------------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

s.addText(
  LINES.map((t, i) => ({ text: t, options: { breakLine: i < LINES.length - 1 } })),
  {
    x: 1.0, y: 2.0, w: 10.0, h: 4 * PITCH / 72 + 0.2,   // box tall enough for pinned pitch
    fontSize: 20, fontFace: "Arial", color: "333333",
    lineSpacing: PITCH,        // <-- THE PIN (single knob; no paraSpaceAfter)
    margin: 0,
  }
);

// spacer-line example (empty-run pitfall): use " " at an explicit small size
s.addText(
  [
    { text: "caption top", options: { breakLine: true } },
    { text: " ", options: { fontSize: 8, breakLine: true } },   // NOT "" — empty runs drop fontSize
    { text: "caption bottom", options: {} },
  ],
  { x: 1.0, y: 6.0, w: 10.0, h: 1.0, fontSize: 14, fontFace: "Arial",
    color: "333333", lineSpacing: 18, margin: 0 }
);

pres.writeFile({ fileName: "demo_line-spacing.pptx" })
  .then(() => console.log("wrote demo_line-spacing.pptx"));
