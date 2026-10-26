# final-deck-merge — continuous combined deck

The combined deck `<deck>_final.pptx` is a CONTINUOUS ARTIFACT, not an
end-of-program batch job; it is initialized at approval time and updated in place

## Lifecycle

1. **INIT (MODE=placeholder)** — runs the moment the owner approves the
   unique-frame set (the HARD STOP lifts; NEVER on an unapproved set).
   Build N pages, one per confirmed frame in printed-badge order, each page
   the original frame image full-bleed (LAYOUT_WIDE 13.33x7.5in; 960x540
   frames fit exactly). Write `final_deck_state.json`: per page
   `{page, status: "placeholder", source_image, image_md5, updated_at}`.
2. **UPDATE (MODE=update <N>)** — after slide N certifies
   (`gen_status='passed'` AND `visual_check='PASS'`), replace page N with the
   certified `slide_NNN_recreated.pptx` content AT THE OPC PACKAGE LEVEL:
   slide XML verbatim, per-slide rels retargeted, media renamed per slide
   (`imgNNN_<orig>`), skeleton parts md5-checked, [Content_Types].xml and
   presentation.xml.rels adjusted for the replaced page. Never re-encode,
   never rebuild certified content. Flip the page's ledger row to
   `certified` with the source deck's md5; bump the deck md5 record.
3. **CLOSE** — when every page is `certified`, run the gate (example.sh):
   render the combined deck + every source in ONE soffice session
   (project TMPDIR, never /tmp), pixel-diff page N vs source N — 0/N
   mismatches required — then bank md5 + gate report. The close-time FULL
   merge may still be run as a cross-check; if it differs from the
   continuously-updated deck, treat it as a defect in the update path, not
   a reason to prefer one side silently.

## Invariants

- Page count is CONSTANT from init: exactly the confirmed frame count.
- Page order is CONSTANT: printed-badge order (the slides_index order).
- A certified page's content in the combined deck is byte-identical to its
  per-slide deck's content (the pixel gate proves it at close; per-update
  render checks prove it as you go).
- Placeholder pages are NEVER shipped silently at close: the gate only runs
  when the ledger shows all pages certified.
- The deck file is written atomically (temp + rename) and its md5 banked
  after every update, so a crashed update never leaves a torn package.
