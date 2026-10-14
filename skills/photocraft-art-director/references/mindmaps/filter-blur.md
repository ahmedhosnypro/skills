# filter-blur

- `filter.blur.average` — Fills the selection (or whole layer) with its single alpha-weighted mean colour — choose it to sample a dominant palette swatch or flood an area with a mood colour, not to soften anything.
- `filter.blur.blur` — Fixed-strength light gaussian soften (equivalent radius about 0.6 px) with no dialog — choose it for a barely-there anti-crisp pass, e.g. calming jaggies on rasterized shapes or edges that read one notch too sharp.
- `filter.blur.blurMore` — Fixed-strength next-notch soften — the 3x3 kernel [1 2 1; 2 2 2; 1 2 1]/14 matched to the reference app's Blur More response — choose it when one-step Blur is too faint and a dialog filter is overkill.
- `filter.blur.boxBlur` — Averages each pixel over a plain square window of the given radius — choose it over gaussianBlur when you want a flat, even softening with no bell-curve weighting: mechanical soft-focus, cheap big-radius haze, or a flatter bokeh smear.
- `filter.blur.gaussianBlur` — The default bell-curve blur: melts detail into a smooth weighted falloff — choose it for glow beds, atmospheric haze, softening rasterized strokes, depth-graded edge softness, and anything where 'blur it' is meant.
- `filter.blur.lensBlur` — Camera-style bokeh: blurs by a depth map so near/far planes melt differently, with a polygonal aperture shaping highlights — choose it for believable depth-of-field, shaped bokeh balls, or true photographic falloff that a flat gaussian cannot fake.
- `filter.blur.motionBlur` — Smears the layer along one angle for a fixed pixel distance — choose it for speed streaks, rain or wind direction, water reflection smear, or any linear energy the scene needs.
- `filter.blur.radialBlur` — Blurs in arcs around a centre (spin) or outward from it (zoom) — choose it for wheel-spin, vortex energy, warp-speed zoom bursts, or radiating light rays.
- `filter.blur.shapeBlur` — Averages over a kernel shaped as circle, ring, square, diamond, triangle, hexagon, star, heart or cross — choose it when the blur itself should carry a silhouette: heart-softened romance tints, star-softened sparkle fields, cross-flare glows.
- `filter.blur.smartBlur` — Smooths flat areas while keeping edges crisp, and can even draw the edges back as ink — choose it to clean grainy fills without losing linework, or in edgeOnly/overlayEdge mode to get a drawn, cel-shaded outline look.
- `filter.blur.surfaceBlur` — Bilateral-style blur: averages only within the threshold so flat areas become silky while edges stay razor-sharp — choose it to clean poster/paper texture, flatten skies, or prep flat-colour art without blurring linework.
- `filter.blurGallery.fieldBlur` — Places blur-amount pins on the image and smoothly blends between them — choose it for hand-authored depth: sharp subject, soft corners, graded mist bands, all in one call.
- `filter.blurGallery.irisBlur` — Keeps an elliptical (superelliptical) core pin-sharp and blurs everything outside it, feathering between — choose it for a one-call subject spotlight: sharp face or boat, melted world around it.
- `filter.blurGallery.pathBlur` — Streaks each pixel along the direction of the nearest drawn path, with per-path length and taper — choose it for flowing energy that follows a shape: comet tails, wind flow along a ridge, river streaks, light trails.
- `filter.blurGallery.spinBlur` — Rotates the content of each pin's ellipse about its centre by an arc of blurAngle degrees, feathered at the rim — choose it for spinning wheels, propellers, swirls, or a turning vortex inside a controlled region.
- `filter.blurGallery.tiltShift` — Keeps a straight band through the chosen centre sharp and blurs with distance beyond it, graded over a transition width — choose it for miniature-world looks, horizon-locked focus, or a clean sharp-corridor through a busy scene.

Full params, traps, and evidence for each command live in the search index:
`python3 indexer/mind_index.py search "<command>"`
