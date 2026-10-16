// Pattern: delimiters-bezier-png — embed side.
// Embeds a Bézier-rendered delimiter PNG (from gen_delimiter.py) at EXACT size.
// Run:
//   python3 gen_delimiter.py lp 48 2.5 B3B3B3 paren_left.png
//   python3 gen_delimiter.py rp 48 2.5 B3B3B3 paren_right.png
//   NODE_PATH=$(npm root -g) node example.js   -> demo_bezier-paren.pptx
//
// LAWS:
// - addImage at EXACT size: w = px_w/600 in, h = px_h/600 in — NEVER rescale.
// - Anchoring: "lp" lands the ink LEFT edge (= stroke bulge outer edge) on the
//   measured stroke column; "rp" lands the ink RIGHT edge; y so ink_top equals
//   the measured block top. Compute from the sidecar, never eyeball.
// - Closed loop before judging: measure the delimiter ink extent in the render
//   vs the computed extent (~4px tolerance at 150dpi) and assert NO enclosed-text
//   ink inside the delimiter stroke columns (stroke-to-text gap per original).
// - Pin lineSpacing on the enclosed multi-line column (see explicit-line-spacing)
//   and assert the delimiter ink covers the block's bottom-most INK row.
// - Per-class COLOR is a legitimate parameter (sidecar geometry is byte-identical
//   between colors — recoloring = zero repositioning risk).

const fs = require("fs");
const pptxgen = require("pptxgenjs");

// ---- parameters ------------------------------------------------------------
const LEFT  = JSON.parse(fs.readFileSync("paren_left.json"));   // sidecar from gen_delimiter.py
const RIGHT = JSON.parse(fs.readFileSync("paren_right.json"));
const BLOCK = {
  strokeColLeft:  1.0,   // in — measured left-paren stroke column (bulge outer edge)
  strokeColRight: 3.2,   // in — measured right-paren stroke column
  top:            2.0,   // in — measured block ink top
};
const LINES = ["(100, 150, 200)", "(150, 200, 250)"];

// ---- build -------------------------------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

// "lp": ink LEFT edge -> strokeColLeft;  "rp": ink RIGHT edge -> strokeColRight
const xL = BLOCK.strokeColLeft;
const xR = BLOCK.strokeColRight - RIGHT.w_in;
s.addImage({ path: "paren_left.png",  x: xL, y: BLOCK.top, w: LEFT.w_in,  h: LEFT.h_in });
s.addImage({ path: "paren_right.png", x: xR, y: BLOCK.top, w: RIGHT.w_in, h: RIGHT.h_in });

// enclosed block (pinned pitch; ink stays clear of both stroke columns)
s.addText(
  LINES.map((t, i) => ({ text: t, options: { breakLine: i < LINES.length - 1 } })),
  { x: BLOCK.strokeColLeft + 0.15, y: BLOCK.top,
    w: BLOCK.strokeColRight - BLOCK.strokeColLeft - 0.3,
    h: LEFT.h_in, fontSize: 18, fontFace: "Arial", color: "333333",
    lineSpacing: 24, margin: 0 }
);

pres.writeFile({ fileName: "demo_bezier-paren.pptx" })
  .then(() => console.log("wrote demo_bezier-paren.pptx"));
