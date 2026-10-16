// Pattern: inner-frame-budget
// An inner frame is a content container: ALL its content ink must sit INSIDE the
// frame with clearance, in EVERY renderer. Measure first, draw second.
// Run:  NODE_PATH=$(npm root -g) node example.js   -> demo_inner-frame.pptx
// Then run the companion closed-loop checker:
//   python3 check_containment.py demo_inner-frame.pdf frame 2.0 1.5 11.3 6.9
//   (renders the pptx via soffice, then asserts ink is strictly inside the frame)
//
// LAWS:
// - Budget for the TALLEST plausible renderer, not the one you measure with:
//   LibreOffice bare-fit containment is NOT containment in PowerPoint (no text-box
//   clipping + taller line boxes on some systems). Keep >= 0.4in bottom clearance in
//   the LO render for blocks near a frame bottom.
// - If content genuinely needs more room than the frame gives, ENLARGE THE FRAME
//   (raise y start AND/OR increase height) and shift content up rigidly by the same
//   offset — preserves every internal margin. The outer house frame is the hard
//   ceiling: keep >= 0.05in daylight between inner-frame bottom and the house stroke.
// - A frame SHORTER than the original's cannot contain content placed at the
//   original's geometry — reproduce the original's measured frame bottom, or larger.
// - Never compress a text-bearing box below ~1.2 x fontSize of height to "gain" room
//   (trades an LO pass for a PowerPoint overflow).
// - Z-ORDER MASKING: an element drawn later (e.g. a caption box) can HIDE a frame
//   crossing — per-element bbox checks cannot see it. Assert GAP BANDS too: the band
//   between adjacent elements (frame edge <-> image edge, image edge <-> caption)
//   must contain ZERO non-background pixels.
// - Image panels: bake the region borders INTO the generated image (overlay shape
//   borders misalign); re-verify every surrounding frame against the image's ink.

const pptxgen = require("pptxgenjs");

// ---- parameters ------------------------------------------------------------
// Frame geometry (inches) — derive from the ORIGINAL's measured frame region
// (960x540 frame, 1px = 1pt): x=72/72, y=108/72, w=810/72, h=(497-108)/72 ...
const FRAME = { x: 2.0, y: 1.5, w: 9.3, h: 5.4 };   // demo values
const CLEAR = 0.4;                                   // min bottom clearance (in)
const TITLE = "Pattern demo: inner-frame budget";

// ---- build -------------------------------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const s = pres.addSlide();
s.background = { color: "E8E8E8" };

// (house chrome omitted here — see patterns/house-chrome)

// 1. inner frame at measured geometry
s.addShape(pres.shapes.RECTANGLE, {
  x: FRAME.x, y: FRAME.y, w: FRAME.w, h: FRAME.h,
  fill: { type: "none" }, line: { color: "C00000", width: 1.5 },
});

// 2. content: multi-line block sized so its ink clears the frame bottom.
//    Content block height must satisfy: y_content + block_height
//      <= FRAME.y + FRAME.h - CLEAR
const lines = ["first bullet line", "second bullet line", "third bullet line"];
s.addText(lines.map((t, i) => ({
  text: t, options: { breakLine: i < lines.length - 1 },
})), {
  x: FRAME.x + 0.2, y: FRAME.y + 0.2,
  w: FRAME.w - 0.4, h: 2.0,                    // box height << frame bottom - CLEAR
  fontSize: 20, fontFace: "Arial", color: "333333",
  lineSpacing: 24,                             // see patterns/explicit-line-spacing
  margin: 0,
});

// 3. bottom element placed so ink clears the frame bottom with >= CLEAR
const bottomY = FRAME.y + FRAME.h - CLEAR - 0.5;   // 0.5in-tall box, ink inside
s.addText("bottom element (ink must clear the frame line)", {
  x: FRAME.x + 0.2, y: bottomY, w: FRAME.w - 0.4, h: 0.5,
  fontSize: 16, fontFace: "Arial", color: "333333", margin: 0,
});

pres.writeFile({ fileName: "demo_inner-frame.pptx" }).then(() => console.log("wrote demo_inner-frame.pptx"));
