// Pattern: delimiters-straight-bars — matrix/vector delimiter pairs as straight bars
//
// LAW: a delimiter pair around matrices, vectors, and digit stacks — the (..)(..)
// constructs of matrix algebra (row/column vectors, augmented blocks, inner
// products, Jacobian/derivative factors) — is drawn as STRAIGHT VERTICAL BARS:
// one 1pt-wide rectangle per delimiter. NEVER curved, for this construct class:
// no font-glyph parens with a visible bow, no Bézier PNGs, no arc shapes
// (owner directive, absolute). At frame resolution the originals' matrix parens
// are hairline near-straight strokes — a bar IS the faithful form; the bow a
// 20pt+ font glyph carries is a visible defect, not fidelity.
//
// Why bars win here:
//  - Direction-symmetric by construction: the mirroring defect class of the
//    delimiter direction law (references/equations.md) cannot occur — no
//    per-side templates to author.
//  - Identical pixels in LibreOffice and PowerPoint; no glyph metrics, no
//    baseline drift, no PNG rescale laws.
//  - Trivially PIL-verifiable per measured window (companion check_bars.py).
//
// Geometry — everything from the ORIGINAL, per delimiter (1px = 1pt at 960x540):
//  - x = the measured bulge column (extreme-ink x of the original's paren).
//  - y, h = the measured ink-row span of that delimiter (NOT the text line).
//  - fill = the original's measured gray per construct (grays differ per block:
//    909090, A6A6A6, 6E6E6E were all measured on one slide — never reuse one).
//  - w = 1 (frame scale); in the build: w: fw(1).
//
// Bars hug the digits: enclosed digit cells are re-laid to the original's
// measured centroids — per-cell cx on the digit line, cy at the measured
// digit-row center. A high-digit line sits ~14px above a text-line center at
// frame scale (b+13.2 vs b+27 measured on one deck) — measure, never inherit.
//
// Missing pairs are ADDED: when the original parenthesizes a triplet the spec
// or parent build leaves bare ([1 1 1] etc.), draw BOTH bars at the measured
// bulge columns — the original's construction wins over the build's inheritance.
//
// Verification (closed loop, before judging; a judge PASS never waives):
//  - Companion check_bars.py per measured window on the asset band, the 150dpi
//    render crop (--scale 2), and the original-frame crop (ground truth):
//    straightness (per-row centroid within ±1px across the span), span, color.
//  - Zone-diff vs the pre-edit render: changed pixels confined to the delimiter
//    zone, 0 strays.
//  - Precedence: for THIS construct class the bar form supersedes
//    delimiters-bezier-png / delimiters-spanning-arc / delimiters-stretched-glyph
//    / font-glyph parens. Those patterns keep delimiters whose ORIGINAL
//    genuinely curves (multi-row display spans, braces) — measured pixels decide.

function dbar(pptx, slide, fx, fy, fw, fh, x, y, h, color) {
  // fx/fy/fw/fh = the slide build's px->inch scale helpers (1px = 1pt).
  slide.addShape(pptx.ShapeType.rect, {
    x: fx(x), y: fy(y), w: fw(1), h: fh(h),
    fill: { color }, line: { type: "none" },
  });
}

// Worked example — a row-vector product with an added pair + a tall matrix pair.
// All numbers below are EXAMPLE measurements; take yours from the original.
const DELIM_GRAY = "A6A6A6"; // measured green-gray of the small triplet parens
const TALL_GRAY = "909090";  // measured gray of the tall matrix delimiters

// Row-vector triplet "(1 1 1)" re-laid to measured cell centroids, then its pair:
// left bulge x=329, right bulge x=375, row base b=140: bar y = b+7, h = 13.
const cells = [{ t: "1", cx: 334.7 }, { t: "1", cx: 352.6 }, { t: "1", cx: 370.7 }];
for (const c of cells) {
  slide.addText(c.t, { x: fx(c.cx - 5), y: fy(140 + 6), w: fw(10), h: fh(14),
    fontSize: 10, color: "000000", align: "center" });
}
dbar(pptx, s, fx, fy, fw, fh, 329, 140 + 7, 13, DELIM_GRAY); // "(" as a bar
dbar(pptx, s, fx, fy, fw, fh, 375, 140 + 8, 12, DELIM_GRAY); // ")" as a bar

// Tall matrix delimiters around a 6-row block: x = measured bulge columns,
// y/h = the measured ink span of the block (y=180, h=46 here).
dbar(pptx, s, fx, fy, fw, fh, 262, 180, 46, TALL_GRAY); // left of the matrix
dbar(pptx, s, fx, fy, fw, fh, 306, 180, 46, TALL_GRAY); // right of the matrix
