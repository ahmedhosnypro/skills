// Pattern: highlight-box
// A highlight box (tan/yellow frame around text) must CLEAR its text on every
// side. Size from measurement, never from the spec's guess.
// Run:  NODE_PATH=$(npm root -g) node example.js   -> demo_highlight-box.pptx
//
// LAWS:
// - RIGHT-CLEARANCE: the longest line's closing glyph must clear the box's fill
//   edge by >= 4.5pt (for an ~18pt line ending in a tall paren) — a gap < 2pt
//   reads as "touching the border" to a human even though nothing clips.
// - Widen on the RIGHT ONLY (x/y/h unchanged) when fixing a clearance complaint:
//   only the box's right border stroke column moves; every other pixel stays
//   byte-identical, so certification of untouched regions is inherited.
// - Text boxes wrap at BOX width, not ink width: budget every box ~20% beyond
//   the longest line's measured advance so a later widening never re-wraps.
//   (Arial advance ~ 0.556 em per digit — PIL-measure, don't estimate.)
// - LibreOffice re-lays-out a text RUN when its box widens: expect <=1px
//   glyph-AA shifts across the run; ink bands/extents must stay unchanged.

const pptxgen = require("pptxgenjs");

// ---- parameters ----------------------------------------------------------------
// PIL-measured: longest line advance in inches (from the original or the render)
const LONGEST_ADVANCE = 6.4;
const RIGHT_CLEARANCE = 4.5 / 72;             // law: >= 4.5pt to the fill edge
const BOX = {
  x: 1.5, y: 5.0, h: 1.0,
  w: LONGEST_ADVANCE * 1.05 + RIGHT_CLEARANCE, // ~5% slack + clearance
  fill: "FFFF99", border: "BF8F00",
};
const TEXT = "(make them all the same scale)";

// ---- build ----------------------------------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

s.addShape(pres.shapes.RECTANGLE, {
  x: BOX.x, y: BOX.y, w: BOX.w, h: BOX.h,
  fill: { color: BOX.fill }, line: { color: BOX.border, width: 1 },
});

s.addText(TEXT, {
  x: BOX.x, y: BOX.y, w: BOX.w, h: BOX.h,
  // box width >= advance + clearance; the wrap budget is already inside BOX.w
  align: "left", valign: "middle",
  fontSize: 18, fontFace: "Arial", color: "000000", margin: 0.1,
});

pres.writeFile({ fileName: "demo_highlight-box.pptx" })
  .then(() => console.log("wrote demo_highlight-box.pptx"));
