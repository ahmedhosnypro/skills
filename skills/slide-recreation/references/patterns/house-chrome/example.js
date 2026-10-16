// Pattern: house-chrome
// The shared outer template every slide in a house-style deck MUST use.
// Run:  NODE_PATH=$(npm root -g) node example.js   -> demo_house-chrome.pptx
//
// LAWS (non-negotiable):
// - Slide: LAYOUT_WIDE, W=13.33in, H=7.5in, background E8E8E8.
// - Outer red frame: 0.15in inset from every edge (w = W-0.3, h = H-0.3),
//   line C00000 width 1.5, NO visible fill (let the slide bg show).
// - Slide-number badge: oval x:12.48 y:0.30 w:0.5 h:0.5, fill FFF9C4, line FFF9C4
//   width 0.5; numeral = the number PRINTED ON THE ORIGINAL slide image (no padding).
// - Title box: starts y:0.28, x:0.6, w:12.13, horizontally centered.
// - House chrome overrides any spec or judge finding about these elements; a judge
//   discrepancy on frame/badge/title-y is NOT a fix trigger.
// - pptxgenjs: NEVER prefix hex colors with "#", never 8-char hex; set fontFace
//   explicitly everywhere; margin:0 on boxes that align with shapes.

const pptxgen = require("pptxgenjs");

// ---- parameters (adapt per slide) ------------------------------------------
const NUM = 42;                      // badge numeral = printed number on the original
const TITLE = "Pattern demo: house chrome";
const FONT = "Arial";

// ---- build ------------------------------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const W = 13.33, H = 7.5;
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

// 1. outer red house frame (0.15in inset from every edge)
s.addShape(pres.shapes.RECTANGLE, {
  x: 0.15, y: 0.15, w: W - 0.3, h: H - 0.3,
  fill: { type: "none" },
  line: { color: "C00000", width: 1.5 },
});

// 2. slide-number badge (yellow oval + centered bold numeral)
s.addShape(pres.shapes.OVAL, {
  x: 12.48, y: 0.30, w: 0.5, h: 0.5,
  fill: { color: "FFF9C4" }, line: { color: "FFF9C4", width: 0.5 },
});
s.addText(String(NUM), {
  x: 12.48, y: 0.30, w: 0.5, h: 0.5,
  align: "center", valign: "middle",
  fontSize: 18, bold: true, color: "333333", fontFace: FONT, margin: 0,
});

// 3. title box (house position; may be intentionally empty when the original has no title)
s.addText(TITLE, {
  x: 0.6, y: 0.28, w: 12.13, h: 0.55,
  align: "center", valign: "top",
  fontSize: 24, bold: true, color: "C00000", fontFace: FONT, margin: 0,
});

// 4. (demo content — replace with the slide's real content)
s.addText("Slide content goes inside the frame.", {
  x: 1.0, y: 2.0, w: 11.0, h: 0.5, fontSize: 20, color: "333333", fontFace: FONT, margin: 0,
});

pres.writeFile({ fileName: "demo_house-chrome.pptx" }).then(() => console.log("wrote demo_house-chrome.pptx"));
