# mcp-surface

- `cli:batch` — Play an actions file (JSON or Photoshop .atn) over every image in a directory and save results — choose for folder-wide deterministic restyling/export passes.
- `cli:commands` — Print the engine command registry (id, label, menu path) — choose to discover command ids and check they exist before scripting a build.
- `mcp:command_run` — Run any engine command by id with JSON params — the agent workhorse for every paint/filter/layer edit; use it whenever a command id from command_list is known.
- `serve:engine.execute` — Runs one engine command by id on the JSON-lines `photocraft-cli serve` session — the primary way to edit art headlessly; use for every filter, stroke, blend and layer change when driving PhotoCraft without the GUI.
- `cli:convert` — Convert one file between formats (.pcraft/.psd/.png/.jpg/.tif/.webp/.exr/…) — choose as the deterministic out-of-band delivery lane for finished artwork.
- `mcp:doc_close` — Close a document without saving (default: the active one); use it to drop stale duplicate copies of the same file between scripted iteration rounds.
- `serve:jobs.cancel` — Cancels one running background job started with wait:false — use to stop a runaway heavy filter or merge without losing document state.
- `cli:droplet` — Run a recorded droplet (File › Automate › Create Droplet, .pcdroplet) on files and folders — choose to replay a saved automation recipe on new inputs.
- `mcp:doc_export` — Export the document to an explicit path + format under the write root (doc_save with required path); use it for final delivery files (png/jpg/webp/tif/exr/psd) distinct from the working file.
- `serve:doc.exportLayers` — Writes each exported layer of the document as its own file beneath the write root; choose when a composition must ship as per-layer plates (alpha, masks, elements) for external compositing or game/print pipelines.
- `serve:jobs.list` — Lists background jobs (running with progress, then recent done/failed/cancelled) and applies any that finished — use as the polling loop after any wait:false filter or export.
- `cli:info` — Print one file's document JSON (size, mode, depth, layer tree, warnings) — choose to probe artwork structure cheaply before editing.
- `mcp:doc_export_data_sets` — Render every data set of the document as its own flattened file beneath the write root (batch pre-planned, colliding names refused up-front); use it to emit per-variant artwork from variable data in one call.
- `serve:doc.importDataSets` — Reads a CSV of variable data sets from the read root into the document; choose for data-driven art series — one template, many variants (swapped text, pixels, layer visibility).
- `serve:methods` — Returns the array of method names the headless serve session handles — use first to discover the lane's surface before scripting it.
- `cli:mcp` — Expose the PhotoCraft MCP tool surface on stdio — headless engine by default, or a bridge to a running desktop app — choose when wiring PhotoCraft into an MCP client.
- `mcp:doc_export_layers` — Export each exported layer of the document as its own file beneath the write root; use it to harvest per-layer plates, sprites or textures for reuse and compositing elsewhere.
- `serve:doc.inspect` — Returns the layer tree (top to bottom), history, selection and active layer of a document — the ground-truth read before and after every scripted edit, and the source of layer ids for later commands.
- `serve:session.list` — Lists open documents (index, name, size, dirty, revision) plus the active index — use to pick the right canvas by path, never by index, before editing art.
- `cli:run` — Open (or create) one document, run engine commands in order and save — choose for deterministic scripted artwork builds without a server.
- `mcp:doc_import_data_sets` — Import a variable-data CSV from the read root into the document; use it to feed text/pixel/visibility variables that drive templated artwork, then apply or export the sets.
- `serve:doc.new` — Creates a new document (forwards params verbatim to engine `file.new`, defaults 1920x1080 RGB 8-bit white) — the first call of every headless build session.
- `cli:serve` — Keep one headless engine session open and answer JSON-lines on stdio or loopback TCP — choose when a script makes many edits fast (no MCP framing, no per-command start-up).
- `mcp:doc_inspect` — Read document state as JSON — layer tree top-to-bottom, history, selection, active layer; use it as ground truth before and after every scripted edit and to adjudicate audit claims.
- `serve:doc.open` — Opens an image or document file from beneath the automation read root and makes it active; the capability-scoped way to resume a .pcraft/.psd or load a reference into a headless session.
- `mcp:command_batch` — Run several engine commands in one MCP call, in order — choose to cut round trips in scripted builds; not a transaction (no rollback).
- `mcp:doc_new` — Create a new document (defaults 1920x1080 RGB 8-bit white); use it to start the canvas at the brief's dimensions, colour mode and background mood.
- `serve:doc.place` — Places a file from the read root into the document as a Smart Object layer (Place Embedded) — the non-destructive way to collage logos, textures, plates or references onto a canvas.
- `mcp:command_list` — List engine commands with params docs and enablement — choose first, to pick command ids and see why a command is disabled.
- `mcp:doc_open` — Open an image or document file and make it active; use it to resume a saved .pcraft for iterative refinement or to load source plates into the session.
- `serve:doc.render` — Renders the flattened composite as a PNG — with `path` writes it beneath the write root, without returns it base64; the loop-closing visual check after every edit round.
- `mcp:doc_place` — Place a file into the document as a Smart Object layer (Place Embedded); use it to composite reference plates, textures or logos non-destructively.
- `serve:doc.save` — Saves the document — without `path` only a PSD/PSB/.pcraft kept in its own format is written back; with `path` the extension picks the export format; the milestone-backup and delivery step of every build.
- `serve:doc.select` — Makes the document at `index` the active one — required routing whenever more than one document is open in the session; headless-only (the MCP bridge refuses it).
- `serve:engine.commands` — Lists every engine command with id, label, params doc, enablement and disabledReason — the discovery call to resolve exact command ids before scripting edits.
- `mcp:doc_render_preview` — Returns the flattened document as a bounded PNG image — the cheap eyeball-check (and audit input) at every iteration; use after each build/modify pass before spending a vision audit.
- `mcp:doc_save` — Writes the document — .pcraft keeps layers lossless and incremental, any other extension exports; use at every milestone as zero-loss insurance and for the final layered deliverable.
- `mcp:doc_select` — Switches which open document the default-index tools address; use after session_list whenever more than one document is open — but prefer matching by path first.
- `mcp:jobs_cancel` — Stops a runaway or unwanted long job (or all running jobs when job is omitted); the document is left unchanged — the safe abort when a heavy filter pass starts ruining a piece.
- `mcp:jobs_list` — Shows running jobs (progress 0-1, message, elapsed) and the last few finished (done|failed|cancelled with result or error); poll this instead of re-sending a long command.
- `mcp:render_preview` — Same operation as doc_render_preview under the short alias spelling — flattened PNG of the document (bridge: window screenshot); use either name, they share implementation.
- `mcp:session_list` — Reads the open-document table (index, name, size, dirty) plus the active index; the first call of any session and the guard before every edit run.
- `serve:batch` — Executes a list of engine commands or serve methods in one request, in order — the speed lane for scripted build/modify passes (155 commands in ~9 s in the field).
- `serve:doc.close` — Drops a document from the headless session (default the active one) without saving — the cleanup half of session hygiene for scripted lanes.
- `serve:doc.exportDataSets` — Batch-exports the document's variable data sets as one flattened image each beneath the write root — the deterministic way to render a whole variant family (palette-swap series, per-name posters) in one planned pass.

Full params, traps, and evidence for each command live in the search index:
`python3 indexer/mind_index.py search "<command>"`
