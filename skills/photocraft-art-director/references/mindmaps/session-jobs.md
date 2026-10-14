# session-jobs

- `command.list` — Enumerates every engine command with id, label, menu path, shortcut, params doc and whether it can run right now - call first to discover the command surface, or filter when you know roughly what you need.
- `document.activate` — Makes the document at a tab index active so subsequent active-document commands (layer.*, paint.*, filters) target it - switch canvases when juggling several artworks in one session.
- `document.inspect` — Returns the active (or named) document's full state as JSON - size, mode/depth/resolution, layer tree with kinds/opacity/blend/masks/bounds, selection, history, snapshots, channels - the text-only way to verify artwork state without a screenshot.
- `document.move` — Reorders a document's tab position within the session so artboards appear in a chosen order - arrange canvases when a presentation or batch step walks documents by index.
- `document.pixel` — Samples the flattened composite colour at one x,y on the active document - probe whether a gradient, glow or painted stroke actually rendered at a spot without exporting a preview.
- `document.presets.delete` — Removes a saved New-Document preset (canvas size/mode/depth/background configuration) by name - retire an artwork format preset you no longer need.
- `document.presets.get` — Returns one saved document preset plus ready-to-use `file.new` params for it - look up an artwork's canvas recipe (size, mode, depth, background) before recreating that format.
- `document.presets.list` — Lists every saved New-Document preset with its full settings - see which canvas formats exist before creating artwork or saving a near-duplicate.
- `document.presets.save` — Stores a named New-Document configuration (size, resolution, colour mode, depth, background) so an artwork format can be recreated exactly - save a canvas recipe once, reuse it for a whole series.
- `document.recent.add` — Records a New-Document settings set at the top of the Recent list (File > New) so a recently used canvas recipe can be re-picked - normally automatic from file.new; call directly only to seed the list.
- `document.recent.list` — Returns the recent File-New document settings (newest first) so a client can re-create a canvas at a previously used size/mode; choose when repeating a prior canvas setup.
- `document.sampleColor` — Reads the colour under a document point like the Eyedropper - one pixel or the averaged NxN square around it, from chosen layers; choose to pick palette colours or verify rendered colour.
- `jobs.cancel` — Cancel one running background job by id — or every running job when `job` is omitted; stops a long filter/Photomerge whose look you already judge wrong and unlocks its document at once.
- `history.deleteSnapshot` — Removes a named session snapshot; the document and its history states are untouched; choose when cleaning up checkpoint clutter.
- `jobs.list` — Report every running background job plus the last 16 that ended (state, progress, message, elapsed, result/error); poll it to wait out a `wait:false` long command or triage a stuck one.
- `history.deleteState` — History panel trash: drops a state and every later one; the document returns to the state before and the deleted steps can't be redone; choose to rewind-and-discard experiment steps permanently.
- `session.inspect` — Cheap JSON snapshot of the whole session — active document index, every open document (name/path/size/dirty/revision) and FG/BG colors; call it first to discover documents before driving one.
- `history.newDocument` — Copies the document as it was at a history state into a fresh untitled document with its own history; choose to fork an artwork variant from an earlier stage without touching the original.
- `history.newSnapshot` — Named copy of the document for the session (the camera button) that is NOT a history step; choose to pin a named checkpoint before risky edits.
- `history.redo` — Steps history forward one state - namespace alias of edit.redo; choose when driving by History naming (edit.* stays the menu item and owns the shortcuts).
- `history.renameSnapshot` — Renames a session snapshot (double-click its name); choose to label checkpoints meaningfully, e.g. "Lesson start" or "Before recolour".
- `history.selectSnapshot` — Returns the document to a snapshot as ONE new undoable state named after it; choose to restore a pinned checkpoint while keeping undo.
- `history.undo` — Steps history back one state - namespace alias of edit.undo; choose when driving by History naming (edit.* stays the menu item and owns the shortcuts).

Full params, traps, and evidence for each command live in the search index:
`python3 indexer/mind_index.py search "<command>"`
