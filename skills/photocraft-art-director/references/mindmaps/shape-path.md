# shape-path

- `path.addAnchor` — Inserts an anchor on a segment at parameter t without changing the curve's shape - use to add control points while refining silhouettes, contours and outline art.
- `path.moveAnchors` — Moves one or more bezier anchors (with their handles) by an offset — the Direct-Selection drag; choose to reshape curves, nudge silhouettes, or reposition vector shapes in one undoable step.
- `path.bendSegment` — Bends or drags the segment leaving a knot by a pixel offset - use to sculpt curve bellies (cloud outlines, fabric folds, wave horizons) or slide straight edges.
- `path.moveHandle` — Moves one bezier direction handle to an absolute point — pulls a curve into a bulge or breaks a smooth point into a corner; choose for calligraphic bends, easing a curve, or sharpening a silhouette corner.
- `path.transform` — Affine-, quad- or warp-transforms a work/saved/layer path; choose to reposition, perspective-warp or bend drawn vector art without re-drawing knots.
- `path.clippingPath.clear` — Removes the document's clipping path so PSD export no longer embeds a cut-out path - use when a saved silhouette should stop travelling with the file.
- `path.set` — Creates or replaces the work path or a named path from a path JSON (knots with optional in/out handles); with `op` it appends subpaths under a boolean op — the foundation for building precise geometric art from coordinates.
- `shape.create` — Creates a live vector shape layer (rect/roundedRect/ellipse/polygon/star/line) or an arbitrary knot path; choose for geometric backgrounds, badges, logos and silhouettes built from scratch.
- `path.clippingPath.set` — Marks a saved path as the document's clipping path for PSD export - use to ship a cut-out silhouette inside a PSD for print and layout apps.
- `path.stroke` — Paints the brush, pencil, eraser or any paint/retouch tool along the path's exact geometry onto a pixel layer — choose for clean hand-guided inking, glow rim-strokes, or retouching precisely along an edge.
- `shape.edit` — Edits an existing shape layer in place: regenerate live geometry, replace the path, move/transform, set subpath combine-ops, fill rule, fill and stroke; choose when refining a shape without recreating it.
- `path.convertPoint` — Switches an anchor between corner and smooth - use to sharpen a rounded corner or soften a hard angle in logos, lettering and outline art.
- `path.rename` — Renames a saved path, or — when `name` is the work path — saves it as a named path (Photoshop semantics); choose to persist the work path before further edits or to organise paths for clipping/export.
- `shape.info` — Reads a shape layer's path, fill, stroke, live params and rendered bounds; choose before editing to see exact geometry and current style.
- `path.delete` — Removes the work path or a named saved path from the document - use to clean up scratch outlines or discard an unused cut-out path.
- `path.style.copyFill` — Copies the active shape layer's fill (solid, gradient or pattern) to the session clipboard — choose to clone one fill across a family of vector shapes for colour consistency.
- `shape.rasterize` — Converts a shape layer into a pixel raster layer; choose when vector art must feed pixel filters, blend modes, masks or flattening.
- `path.deleteAnchor` — Removes an anchor and joins its neighbours, keeping their handles - use to simplify over-traced outlines or erase stray knots from vector art.
- `path.style.copyStroke` — Copies the active shape layer's complete stroke (width, colour, caps, dashes) to the session clipboard — choose to clone an outline style across shapes so linework matches everywhere.
- `shape.presets.list` — Lists custom-shape preset groups with each shape's name and subpath count; choose to discover available motifs before placing one.
- `path.fill` — Rasterizes a path and paints it onto a pixel layer with colour, blend mode, opacity and feather - use to lay flat colour inside a silhouette (skies, shape backdrops, soft blobs) without making a selection first.
- `path.style.pasteFill` — Pastes a previously copied shape fill onto the target shape layer — the applying half of the fill-clipboard pair; choose to propagate one fill to many silhouettes fast.
- `shape.presets.place` — Places a named preset shape as a new (or appended) shape layer, scaled into a rect; choose for decorative stamps — arrows, flourishes, ornaments, badges.
- `path.info` — Reads one path's full bezier geometry - call first to learn subpath/knot indices before any point edit, or to capture an outline's exact anchor and handle data.
- `path.style.pasteStroke` — Pastes a previously copied complete stroke onto the target shape layer — the applying half of the stroke-clipboard pair; choose to re-ink several shapes with one identical outline.
- `shape.presets.new` — Saves a path — inline, the work path, the active shape layer's path or a vector mask — as a named custom-shape preset; choose to turn drawn art into reusable stamps.
- `path.list` — Enumerates the document's paths (saved, work, clipping, active layer's shape path / vector mask) with knot counts - the discovery call before reading or editing any path.
- `path.toSelection` — Converts a path (work, saved, or the active layer's shape path / vector mask) into a pixel selection — choose to restrict painting, filters and adjustments to a precise vector outline (Cmd+Enter).
- `shape.presets.edit` — Batch-edits the shape-preset library (rename/delete/move presets and groups, new/rename/delete group); choose to curate or import motif packs.
- `shape.presets.reset` — Resets the shape-preset library to PhotoCraft defaults, optionally appending after existing groups; choose after import or curation mistakes.

Full params, traps, and evidence for each command live in the search index:
`python3 indexer/mind_index.py search "<command>"`
