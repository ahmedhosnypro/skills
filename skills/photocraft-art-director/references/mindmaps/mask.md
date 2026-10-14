# mask

- `channel.delete` — Deletes an alpha or spot channel by index or name (default: the targeted one); choose when a saved matte is no longer needed or before final export.
- `channel.duplicate` — Copies an alpha channel (or a colour/composite/Quick-Mask plane) into a new channel, another open document, or a new grayscale document; choose to back up a matte or mint an inverted one.
- `layer.layerMask.apply` — Bakes the layer's pixel mask into pixel alpha and deletes the mask — choose when a masked composite is final and must survive mask-unaware tools or export.
- `channel.list` — Reads the Channels panel: composite name, colour rows, every alpha/spot channel (index, name, eye state, spot colour/solidity, overlay colour/opacity), Quick Mask and the current target; call before addressing channels.
- `layer.layerMask.delete` — Discards the layer's pixel mask without applying it — choose to abandon a masking experiment and restore the layer's original transparency exactly.
- `channel.merge` — Combines open same-size grayscale documents into one RGB/CMYK/Lab image (extras become alpha channels) and closes the sources; choose for channel-as-plate workflows, e.g. recombining split plates or night-sky separations.
- `layer.layerMask.edit` — Sets mask Density (%) and Feather (px) without touching mask pixels — choose to soften mask edges or mute mask strength non-destructively, after the mask exists.
- `channel.mergeSpot` — Prints a spot ink into the colour channels over a flattened image and deletes the spot channel; choose when handing spot-colour art to a flat export or proofing the ink visually.
- `layer.layerMask.enabled` — Toggles (or explicitly sets) the pixel mask's enabled flag — choose to compare with/without the mask or pause it while keeping every painted mask value.
- `channel.move` — Moves an alpha channel to a new slot in the Channels panel; choose purely to organise saved mattes (the view target and eyes are remapped).
- `layer.layerMask.fromTransparency` — Converts the layer's alpha into a new pixel mask and makes the pixels fully opaque — choose to turn a hard cutout into a paintable, featherable grayscale mask.
- `channel.new` — Creates an alpha channel (saved grayscale matte, white = selected), optionally seeded from the current selection, and targets it for immediate painting; choose to stash or hand-build masks.
- `layer.layerMask.hideAll` — Adds a black mask that hides the whole layer — choose when building a reveal from nothing by painting white (fade-ins, montage build-up, double exposure).
- `channel.newSpot` — Creates a spot-colour channel (a named press ink plate such as gold foil) optionally seeded from the selection; choose when artwork must carry a separate ink.
- `layer.layerMask.hideSelection` — Adds a mask that hides the selected area, then clears the selection — choose to punch a non-destructive hole exactly where a marquee/wand/subject selection lands.
- `channel.options` — Edits a channel's options in place — name, overlay tint colour/opacity, masked-vs-selected side — or promotes an alpha channel to a spot plate (with solidity); also retunes the Quick Mask overlay for the session.
- `layer.layerMask.linked` — Toggles (or sets) whether the pixel mask moves with the layer — unlink to slide content under a fixed mask aperture (windows, frames, parallax reveals).
- `channel.rename` — Renames an alpha channel; choose to keep matte inventories searchable by meaningful names.
- `layer.layerMask.revealAll` — Adds a white mask that reveals the whole layer — the default non-destructive masking start: paint black to hide, gray to veil.
- `channel.setVisible` — Toggles Channels-panel eyes: show an alpha/spot plate alone as a grayscale view, hide colour channels, or reveal the Quick Mask; choose to preview mattes or judge a single plate.
- `layer.layerMask.revealSelection` — Turns the active selection into a mask that shows only the selected area — the standard bridge from select.* (subject/sky/wand/luminosity) to non-destructive isolation.
- `channel.split` — Splits the image into one grayscale document per colour channel plus one per alpha channel, closing the original; choose for per-plate grading or channel-as-mask workflows.
- `layer.toggleMaskOverlay` — Shows/hides the active layer's mask as a 50% red rubylith over the composite (the backslash key) — choose to see exactly which areas the mask hides while you paint it.
- `channel.target` — Sets which channel pixel commands edit — composite, one colour channel, an alpha channel, the layer mask or the vector mask — and retargets the panel; the gateway for channel-scoped and mask-scoped editing.
- `layer.vectorMask.add` — Attaches a resolution-independent path mask to a layer — choose over pixel masks when edges must stay razor-crisp and re-editable (architecture, logos, hard geometry).
- `channel.target.composite` — Targets the composite (RGB) channel — back to editing all colour channels at once; choose after any channel-scoped edit (⌘2).
- `layer.vectorMask.currentPath` — Applies the current work path (or a saved path) as the layer's vector mask — the one-step 'make this path mask the layer' after drawing a silhouette.
- `channel.target.layerMask` — Targets the active layer's layer mask (⌘\) so paint, filters and adjustments edit the mask instead of the art; choose for hand-carving mattes — soft fog edges, reveal/hide zones.
- `layer.vectorMask.delete` — Removes the layer's vector mask entirely (pixels untouched) — choose when the geometric hiding is no longer needed or is being baked in via rasterize instead.
- `channel.target.slot3` — Targets the first colour channel after the composite — Red in RGB — via ⌘3; grading or filtering Red alone tints shadows/tones channel-by-channel. (⌘3).
- `layer.vectorMask.edit` — Rewrites a vector mask's path and properties (enabled/linked/density/feather/invert) in one step — choose to retune a geometric mask non-destructively.
- `channel.target.slot4` — Targets the Green channel via ⌘4; the green plane usually carries the most luminance detail — grade or blur it alone for organic colour shifts. (⌘4).
- `layer.vectorMask.enabled` — Toggles (or sets) the vector mask's enabled flag — choose to compare the layer with and without its geometric mask, or gate which mask acts while keeping both.
- `channel.target.slot5` — Targets the Blue channel via ⌘5; the blue plane carries grain/sky — boosting or blurring Blue alone gives classic night-sky and film-grain looks. (⌘5).
- `layer.vectorMask.fromPath` — Turns the named document path (default the work path) into the layer's vector mask — the scripted twin of vectorMask.currentPath for path-to-mask pipelines.
- `channel.target.slot6` — Targets the fourth post-composite row: in RGB the first alpha channel; in CMYK the Black plate; choose to paint a matte via keyboard speed. (⌘6).
- `layer.vectorMask.hideAll` — Adds an inverted, hide-everything vector mask — choose to build visibility from nothing: the shapes you draw on it reveal the layer.
- `channel.target.slot7` — Targets the second alpha channel in RGB (first alpha in CMYK); keyboard-speed matte editing. (⌘7).
- `layer.vectorMask.info` — Reads back a layer's vector mask (path, enabled, linked, density, feather) without changing anything — the check-before-edit probe for geometric masks.
- `channel.target.slot8` — Targets the third alpha channel in RGB (second in CMYK); keyboard-speed matte editing. (⌘8).
- `layer.vectorMask.linked` — Toggles (or sets) whether the vector mask travels with the layer — unlink to slide contents under a fixed geometric aperture.
- `channel.target.slot9` — Targets the fourth alpha channel in RGB (third in CMYK); keyboard-speed matte editing. (⌘9).
- `layer.vectorMask.revealAll` — Adds a non-inverted empty vector mask (reveals everything) — the non-destructive start for hiding later with subtract/intersect path shapes.
- `select.loadLuminosity` — Loads the composite's luminosity as the active selection — the entry point of luminosity-mask workflows: load, refine, then Reveal Selection onto a mask.
- `view.layerMask` — Shows the active layer's mask alone in grayscale or as a rubylith overlay — choose to inspect the mask surface or hand-paint the mask directly.

Full params, traps, and evidence for each command live in the search index:
`python3 indexer/mind_index.py search "<command>"`
