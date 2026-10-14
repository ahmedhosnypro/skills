# gradient-fill

- `edit.fill` — Photoshop's Fill dialog as one command: fill the selection (or whole canvas) with colour/pattern/content-aware/history, choose when you need a controlled flat field, substrate or opaque backdrop.
- `edit.clear` — Delete-key clear: erase the selection to transparency (background colour on a Background layer, or fill the targeted alpha channel/Quick Mask instead) — choose for in-place erase + repaint loops.
- `gradient.presets.list` — Lists every gradient preset group plus the Gradient tool's current gradient — call first to see valid preset names before referencing them.
- `edit.fillForeground` — Instantly fill the selection or whole layer with the foreground colour — the fastest way to lay a flat field of the current pick without opening any dialog.
- `gradient.presets.select` — Sets the Gradient tool's current gradient from a preset or explicit stops — and by default also recolours a selected Gradient Fill layer.
- `edit.fillBackground` — Instantly fill the selection or whole layer with the background colour — pair with the foreground key for two-tone passes without touching tools.
- `gradient.presets.stop` — Adds, moves, deletes or recolours stops — and edits opacity stops — of the Gradient tool's current gradient, without touching any layer.
- `edit.fillForegroundPreserve` — Fill with the foreground colour only where pixels already exist — recolour a silhouette or painted shape in place without touching its transparent surround.
- `gradient.presets.apply` — Creates a non-destructive Gradient Fill layer from a preset (or inline stops) with angle/scale/style/reverse — the fastest way to lay a library ramp on the canvas.
- `edit.fillBackgroundPreserve` — Fill with the background colour only inside existing pixels — the tonal twin of the foreground-preserve key for regrading silhouettes with the background pick.
- `gradient.fill.create` — Creates a live Gradient Fill layer above the active layer from explicit start/end points, masked by the selection — the Gradient tool's non-destructive mode.
- `edit.fillHistory` — Fill the selection with pixels from an earlier history state — the History Brush source by default — for reverting regions to an older look without undoing the whole document.
- `gradient.fill.get` — Returns a Gradient Fill layer's full definition — style, angle/scale/offset, resolved from/to handles, colour + opacity stops, midpoints.
- `gradient.fill.set` — Re-geometries or re-colours an existing live gradient in one command — move handles, change style/scale/offset, swap stops, transparency or midpoints — without recreating the layer.
- `layer.newFillLayer.solidColor` — Add a live Solid Color fill layer above the active layer — a re-editable flat colour veil masked by the selection or a path — choose it over edit.fill when the tone must stay adjustable.
- `gradient.fill.stop` — Surgical single-stop edits on a live gradient: add/move/delete/recolour colour stops, add/move/delete/set opacity stops, or move a segment midpoint.
- `layer.newFillLayer.gradient` — Add a live Gradient fill layer above the active layer with a two-stop from→to gradient — the base tool for skies, water and any smooth colour transition that stays editable.
- `gradient.presets.new` — Stores the Gradient tool's current gradient (or explicit stops) as a named preset in a group for reuse.
- `layer.newFillLayer.pattern` — Add a live Pattern fill layer above the active layer, tiling a library pattern at chosen scale/angle — for textures (bricks, grid, checkerboard, paper) that stay re-editable.
- `gradient.presets.edit` — Panel housekeeping: rename, delete or move presets, and create, rename or delete preset groups.
- `layer.fill.solidColor.set` — Change the colour of an existing Solid Color fill layer — the re-tune handle for the tone veils created by layer.newFillLayer.solidColor.
- `gradient.presets.reset` — Replaces — or appends — the preset library with the built-in groups; the undo for a mangled Gradients panel.
- `layer.fill.pattern.set` — Re-tune an existing Pattern fill layer — swap the pattern or adjust scale, angle, link and phase in one undoable step that keeps the layer's masks intact.
- `gradient.presets.importGrd` — Adds every usable gradient from a Photoshop .grd file (version 5) to the Gradients panel as one new group.

Full params, traps, and evidence for each command live in the search index:
`python3 indexer/mind_index.py search "<command>"`
