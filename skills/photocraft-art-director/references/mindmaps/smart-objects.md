# smart-objects

- `layer.smartFilter.blendingOptions` — Set one smart filter's blend mode and opacity; choose when a filter needs integrating (e.g. glow at Screen 60%) instead of running at full strength.
- `layer.smartObjects.relinkToFile` — Points a smart object at a file on disk as its new Linked source; choose it to swap the placed source art while every instance keeps its transform and smart filters.
- `layer.smartFilter.clearSmartFilters` — Remove every smart filter and the filter mask from a smart object, restoring the clean placed source; choose when an effect experiment fails wholesale.
- `layer.smartObjects.convertToSmartObject` — Bundles the active layer (or several selected layers) into one re-editable Smart Object so filters, warps and transforms stay non-destructive; choose it before filtering non-pixel layers.
- `layer.smartObjects.replaceContents` — Swaps the artwork inside a smart object for another file as a new Embedded source; choose it to re-render a placed frame/mockup/texture with new source art while transform, warp and smart filters survive.
- `layer.smartFilter.delete` — Remove one smart filter from the stack (default: the top one); choose when a single effect no longer serves the look.
- `layer.smartObjects.newSmartObjectViaCopy` — Duplicates a smart object with fully independent contents so the copy can be recolored, warped or re-edited without touching the original; choose it whenever you need a second instance that diverges.
- `layer.smartObjects.revealInFinder` — Opens the platform file manager with a linked smart object's file selected; choose it to hand the artist the exact source file behind a linked placement.
- `layer.smartFilter.deleteFilterMask` — Remove the smart filter mask so the whole filter stack applies everywhere on the object; choose when a masked effect should go global.
- `layer.smartObjects.editContents` — Opens a smart object's contents as its own document; save (saveContents) or close it and the placed instance re-renders — the route for in-place re-editing of placed artwork.
- `layer.smartObjects.saveContents` — Writes the open Edit Contents document back into every parent smart object instance as one undoable step; choose it to push in-place edits of placed art into the parent composition.
- `layer.smartFilter.disableFilterMask` — Toggle the filter mask on/off without deleting it (disabled = full filter stack shows everywhere); choose to A/B a masked effect against its unmasked version.
- `layer.smartObjects.exportContents` — Writes a smart object's source file to disk — as-is with the same extension, or converted when the path names another format; use it to extract or hand off the embedded artwork.
- `layer.smartObjects.stackMode.entropy` — Combines a smart object's internal layer stack per pixel into Shannon entropy (bits, normalized over log2 of frame count); choose it to map where the stack varies most — motion, change, texture disorder.
- `layer.smartFilter.disableSmartFilters` — Turn the whole smart-filter stack off (or back on) at one master switch, per-filter eye icons untouched; choose for a clean before/after of all effects.
- `layer.smartObjects.convertToEmbedded` — Pulls a linked smart object's file bytes into the document so it becomes self-contained; choose it before sharing or moving a document so links cannot break.
- `layer.smartObjects.stackMode.kurtosis` — Combines a smart object's internal layer stack per pixel into kurtosis (peakedness of the stack samples); choose it to find pixels where one frame is a strong outlier against the rest.
- `layer.smartFilter.move` — Reorder one filter within the stack; order matters because each filter runs on the previous filter's output — choose when e.g. grain must land above a blur, not under it.
- `layer.smartObjects.convertToLinked` — Writes a smart object's contents to a file and relinks the instance to it, keeping big assets out of the document; choose it to slim a document or share one asset file across documents.
- `layer.smartObjects.stackMode.maximum` — Combines a smart object's internal layer stack per pixel by taking the brightest sample per channel; choose it for lighten-stacking — star trails, light-painting build-up, capturing the brightest variant.
- `layer.smartFilter.setParams` — Retune a stored filter's parameters in place (JSON merged into the existing set); choose for non-destructive iteration — re-tighten a glow radius or shift a grade without re-recording the filter.
- `layer.smartObjects.convertToLayers` — Unpacks a smart object back into plain layers at its placement — a single layer, or a group named after the smart object; use it to hand over editable layers or bake a finished composition.
- `layer.smartObjects.stackMode.mean` — Averages a smart object's internal layer stack per pixel; choose it to reduce noise or ghost-free blend across aligned variants, or to fuse variants into one soft average.
- `layer.smartFilter.setVisible` — Toggle one filter's eye icon in the stack (default: toggle); choose to A/B a single effect's contribution or park a too-strong effect instead of deleting it.
- `layer.smartObjects.rasterize` — Bakes a smart object — its transform, warp and smart filters — into plain pixels; use it to freeze a finished look or to escape the smart-object pipeline before pixel-only work.
- `layer.smartObjects.stackMode.median` — Takes the middle sample per pixel across a smart object's internal layer stack; choose it to erase moving objects ('passers-by'), dust or transient artifacts from a stack of aligned frames.
- `layer.smartFilter.transfer` — Move (or, with copy, duplicate) one filter or the whole stack from one smart object to another in one undoable step; choose to reuse a tuned effect recipe on sibling layers.
- `layer.smartObjects.puppetWarp` — Pins an opaque mesh over the smart object and drags pins to bend, sway or re-pose its content organically; stored as a re-editable smart filter, so choose it over rasterize-and-liquify for natural deformation.
- `layer.smartObjects.stackMode.minimum` — Combines a smart object's internal layer stack per pixel by taking the darkest sample per channel; choose it for darken-stacking — removing bright moving objects, deepening shadows, dark-field fusion.
- `layer.smartObjects.updateModifiedContent` — Force re-render of one linked smart object from its file NOW, even if PhotoCraft thinks it is unchanged; choose it to pull in a linked file that changed while the document was closed.
- `layer.smartObjects.perspectiveWarp` — Maps the smart object through four-corner quads to sit flat artwork into a scene's perspective or fix keystone distortion; stored as a re-editable smart filter, so placed posters, signs and screens stay adjustable.
- `layer.smartObjects.updateChanged` — Re-render the active document's linked smart objects whose files changed on disk since last seen (size or mtime); choose it as the agent-safe sync instead of the desktop app's auto-poll.
- `layer.smartObjects.updateAllModifiedContent` — Re-render every linked smart object in the active document from its linked file in one undo step; choose it after batch-editing linked artwork outside PhotoCraft.
- `layer.smartObjects.stackMode.range` — Re-render a smart object as a per-pixel max-minus-min over its source's layers; choose it to turn a multi-layer source (exposures, animation frames) into a change/energy map.
- `layer.smartObjects.stackMode.skewness` — Per-pixel distribution asymmetry across a smart object's source layers, remapped to a 0..1 grey image (0.5 = symmetric); choose it for eerie mid-tone statistical textures.
- `layer.smartObjects.stackMode.standardDeviation` — Per-pixel spread across a smart object's source layers as a glowing change map; choose it to make motion, edges and misalignment of a stack bloom bright.
- `layer.smartObjects.stackMode.summation` — Per-pixel sum across a smart object's source layers; choose it to accumulate light — star trails, light painting, long-exposure looks from a frame stack.
- `layer.smartObjects.stackMode.variance` — Per-pixel squared deviation across a smart object's source layers — the raw, harsher change map under Standard Deviation; choose it for punchier disagreement textures.
- `layer.smartObjects.stackMode.none` — Clears a smart object's stack mode and re-renders its source normally; choose it when a statistical stack experiment is done and you want the real artwork back.
- `layer.smartObjects.warp` — Bend a smart object with a Photoshop preset (arc, flag, wave, fisheye…) or a custom Bezier mesh, stored losslessly in source space; choose it for posters/labels that must stay re-editable and never soften.

Full params, traps, and evidence for each command live in the search index:
`python3 indexer/mind_index.py search "<command>"`
