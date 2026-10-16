// Pattern: delimiters-stretched-glyph — embed side.
// Run:
//   python3 gen_delimiter.py "(" 48 21 0000CC paren_left.png
//   python3 gen_delimiter.py ")" 48 21 0000CC paren_right.png
//   NODE_PATH=$(npm root -g) node example.js   -> demo_stretched-glyph.pptx
//
// LAWS: embed at EXACT px/600 size, never rescale horizontally; anchor the ink
// edge to the measured stroke column; assert 0 enclosed-text ink in the stroke
// columns; size the span to the block's bottom-most ink row (descenders!).

const fs = require("fs");
const pptxgen = require("pptxgenjs");

const IMG = { w: 21 / 600, h: 48 / 72 };       // from the generator's output line
const BLOCK = { strokeColLeft: 1.0, strokeColRight: 3.2, top: 2.0 };
const LINES = ["z1 = 0.36 w1", "z2 = 0.08 l1", "z3 = 0.45 w2"];

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

s.addImage({ path: "paren_left.png",  x: BLOCK.strokeColLeft,             y: BLOCK.top, w: IMG.w, h: IMG.h });
s.addImage({ path: "paren_right.png", x: BLOCK.strokeColRight - IMG.w,    y: BLOCK.top, w: IMG.w, h: IMG.h });

s.addText(
  LINES.map((t, i) => ({ text: t, options: { breakLine: i < LINES.length - 1 } })),
  { x: BLOCK.strokeColLeft + 0.15, y: BLOCK.top,
    w: BLOCK.strokeColRight - BLOCK.strokeColLeft - 0.3,
    h: IMG.h, fontSize: 18, fontFace: "Arial", color: "333333",
    lineSpacing: 26, margin: 0 }   // pinned pitch; see explicit-line-spacing
);

pres.writeFile({ fileName: "demo_stretched-glyph.pptx" })
  .then(() => console.log("wrote demo_stretched-glyph.pptx"));
