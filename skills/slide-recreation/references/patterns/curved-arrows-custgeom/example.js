// Pattern: curved-arrows-custgeom
// Faithful curved connector arrows (lecture-diagram branching, tree edges) as
// NATIVE pptxgenjs shapes: one custGeom cubic-bezier stroked path per arrow +
// an explicit triangle shape as the arrowhead. Validated on a certified deck
// (closed-loop centerline <=2.6 frame px, judge PASS on attempt 1).
// Run:  NODE_PATH=$(npm root -g) node example.js   -> demo_curved-arrows.pptx
//
// LAWS:
// - FIT the curve from the ORIGINAL frame first: extract the stroke centerline
//   (per-row cluster centers; per-column where the stroke runs near-horizontal),
//   then least-squares a cubic bezier P0->C1->C2->P3 with t-reprojection
//   (init t by chord length, 6-8 iterations of nearest-point-on-curve).
//   Chord-length-only fitting stalls in local optima on S-curves; give it a
//   sensible init (C1 below-left of start, C2 above-left of end).
// - custGeom points are ABSOLUTE slide positions in INCHES (plain numbers <100
//   are parsed as inches). Set the shape bbox to the FULL SLIDE (x:0,y:0,
//   w:13.333,h:7.5) so absolute points land exactly (path space == shape ext).
// - OMIT the fill option entirely -> pptxgenjs emits <a:noFill/> (open stroked
//   path). Passing fill:{type:'none'} emits EMPTY fill XML -> theme default
//   fill paints the bezier solid. Do not pass fill at all.
// - Points: first point {x,y,moveTo:true}, then {x,y,curve:{type:'cubic',x1,y1,x2,y2}}
//   (control points + endpoint, in inches).
// - ARROWHEADS: draw explicitly as pptxgenjs triangle shapes (flipV for
//   down-pointing) at the ORIGINAL's measured bbox, tip ON the target edge,
//   path ending at the head BASE. Do NOT use line.endArrowType here: tail-end
//   arrows are size-locked to the line width (med ~3x lw) and cannot match a
//   measured 9x13px head, and their orientation follows the path tangent
//   (tilted when the curve arrives diagonally).
// - STROKE: width from the measured stroke (~2.5pt for thin lecture arrows);
//   color = the ORIGINAL stroke's PIL modal (thin strokes JPEG-blend with the
//   panel gray — take the modal of stroke-band pixels, not the darkest pixel).
// - VERIFY closed-loop: the ORIGINAL's centerline points must sit within
//   ~4 frame px of the RENDER's stroke ink (point-to-ink distance, e.g.
//   scipy cKDTree over render stroke pixels). A per-row x-comparison between
//   the two images LIES where the stroke is near-horizontal (dx/dy large):
//   sub-row grid offsets amplify into phantom 10+px deviations.

const pptxgen = require("pptxgenjs");

const px = (v) => v / 72; // frame px (960x540, 1px=1pt) -> inches

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
const slide = pres.addSlide();
slide.background = { color: "FFFFFF" };

// demo: parent box bottom-center (460,194.5) curving down-left to (265.25,262)
slide.addShape(pres.ShapeType.custGeom, {
  x: 0, y: 0, w: 13.333, h: 7.5,            // full-slide bbox; absolute inch points
  line: { color: "7B2B34", width: 2.5 },     // NO fill option -> <a:noFill/>
  points: [
    { x: px(460), y: px(194.5), moveTo: true },
    { x: px(265.25), y: px(262),
      curve: { type: "cubic", x1: px(453.57), y1: px(257.78), x2: px(287.08), y2: px(221.72) } },
  ],
});

// explicit measured arrowhead: down-pointing triangle, tip ON the target edge
slide.addShape(pres.ShapeType.triangle, {
  x: px(260.5), y: px(261.5), w: px(9.5), h: px(13), flipV: true,
  fill: { color: "7B2B34" }, line: { color: "7B2B34", width: 0 },
});

pres.writeFile({ fileName: "/tmp/demo_curved-arrows.pptx" })
  .then(() => console.log("wrote /tmp/demo_curved-arrows.pptx"));
