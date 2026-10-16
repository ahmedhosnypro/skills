// Pattern: delimiters-spanning-arc
// Tall near-straight delimiters (parens spanning N stacked lines) as ONE ARC
// shape per side — for the thin, nearly-vertical stroke look of video-frame parens.
// Run:  NODE_PATH=$(npm root -g) node example.js   -> demo_spanning-arc.pptx
//
// LAWS:
// - A delimiter spanning N lines is ONE shape sized to the whole block — NEVER
//   per-line glyph parens stacked by the text engine (garbage caps top+bottom),
//   and NEVER partial-sweep fat arcs.
// - HALF TURN ONLY: "(" -> angleRange [90, 270], ")" -> [270, 450]. OOXML draws
//   only the middle ~52% of bbox height for quarter-sweep arcs ([135,225] etc.)
//   and the elliptical curvature swings the tips far inward ONTO the text.
// - Geometry from measurement: h = the original's measured paren ink extent
//   (topmost to bottommost enclosed line, incl. subscripts' descenders);
//   w = 2-4 original px (the tip curl); place the bbox x so the stroke BULGE
//   (outer edge) lands on the original's measured stroke column — the tips sit
//   at the bbox's horizontal center.
// - fill: { transparency: 100 } (no fill), line: { width ~2.25, color: measured
//   stroke color — read it from the original's pixels, not the spec's prose }.
// - Stroke-to-text clearance: assert no enclosed-text ink inside the delimiter
//   stroke columns, and per-line gaps match the original (~4-11 orig-px).
// - INK-ROLE COLORS: colors come from the original's pixels per glyph (test
//   darkest-40%-median chroma vs a far-side control stroke to unmask JPEG bleed).
// - A superscript glyph inside the stroke-column set pollutes extent measurement:
//   exclude by a column ceiling below its box, never a row band.

const pptxgen = require("pptxgenjs");

// ---- parameters (from PIL measurement of the original, 1px = 1pt) -------------
const BLOCK = {
  linesTop:    2.0,   // in — topmost enclosed line ink
  linesBottom: 3.5,   // in — bottommost enclosed line ink (incl. descenders)
  leftParenX:  1.0,   // in — original's left-paren stroke column (bulge outer edge)
  rightParenX: 4.5,   // in — original's right-paren stroke column
};
const STROKE_COLOR = "B3B3B3";   // measured neutral gray (read from pixels)
const STROKE_W = 2.25;
const CURL_W = 3 / 72;           // 3 orig-px bbox width (the tip curl)

// ---- build --------------------------------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

const py = BLOCK.linesTop - 0.05;
const ph = (BLOCK.linesBottom - BLOCK.linesTop) + 0.10;

function tallParen(side) {
  // bbox x placed so the BULGE (outer edge) hits the measured stroke column:
  // left paren bulges at bbox-left; right paren at bbox-right.
  const x = side === "lp" ? BLOCK.leftParenX : BLOCK.rightParenX - CURL_W;
  s.addShape(pres.shapes.ARC, {
    x, y: py, w: CURL_W, h: ph,
    angleRange: side === "lp" ? [90, 270] : [270, 450],   // HALF TURN — see laws
    fill: { transparency: 100 },
    line: { color: STROKE_COLOR, width: STROKE_W },
  });
}

tallParen("lp");
tallParen("rp");

// the enclosed multi-line block (pin its lineSpacing — see explicit-line-spacing)
const LINES = ["w1, l1", "w2, l2", "w3, l3", "w4, l4"];
s.addText(
  LINES.map((t, i) => ({ text: t, options: { breakLine: i < LINES.length - 1 } })),
  { x: BLOCK.leftParenX + 0.15, y: BLOCK.linesTop, w: 3.0,
    h: BLOCK.linesBottom - BLOCK.linesTop,
    fontSize: 18, fontFace: "Arial", color: "0000CC",
    lineSpacing: 26, margin: 0 }
);

pres.writeFile({ fileName: "demo_spanning-arc.pptx" })
  .then(() => console.log("wrote demo_spanning-arc.pptx"));
