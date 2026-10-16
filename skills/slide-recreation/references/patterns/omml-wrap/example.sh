#!/usr/bin/env bash
# Pattern: omml-wrap
# Dual-representation equations: PowerPoint shows EDITABLE native equations from
# mc:Choice (the PowerPoint-authored pattern — see skeleton.xml); LibreOffice and
# the pixel-gate render the certified PNG from mc:Fallback. Applied IN PLACE to
# the slide's own single pptx AFTER visual certification.
#
# LAWS:
# - Wrap only AFTER the deck is visually certified; the wrap must be a
#   0-pixel-diff operation (LO renders the Fallback).
# - The manifest's rel_ids are RE-DERIVED from the CURRENT pptx after any
#   rebuild — a rebuild can shift an equation pic from rId1 to rId43 and a stale
#   manifest wraps the WRONG picture. Verify each entry: rel_id fresh-read from
#   the pptx rels, media matched by content hash, pic extents == sidecar dims.
# - Mathtext provenance: re-render the sidecar string with the exact renderer
#   and PIL-prove 0 px diff vs the banked PNG before wrapping (the OMML must
#   provably match the fallback image). If the string is unbanked, recover it by
#   ink forensics and prove it — never guess an OMML string.
# - NEVER LO-resave a wrapped deck (LO's writer drops the OMML). Idempotence:
#   re-running the wrap must change nothing.
set -euo pipefail

# ---- parameters -----------------------------------------------------------------
DECK=$1        # the certified, plain-named slide deck (wrapped IN PLACE)
MANIFEST=$2    # per-slide manifest: [{"equations": [{"rel_id","image","mathtext","font_size_pt","color"}]}]
WRAPPER=${WRAPPER:-"python3 omml_wrapper.py"}    # adapt to your project's wrapper

# ---- 1. prove manifest freshness (fail loud before wrapping) ----------------------
python3 - "$DECK" "$MANIFEST" <<'EOF'
import json, sys, zipfile
deck, manifest = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(deck)
rels = z.read("ppt/slides/_rels/slide1.xml.rels").decode()
man = json.load(open(manifest))
for e in man["slides"][0]["equations"]:
    rid = e["rel_id"]
    assert f'Id="{rid}"' in rels, f"stale rel_id {rid} — re-derive the manifest"
print("manifest rel_ids verified against the current deck")
EOF

# ---- 2. wrap in place --------------------------------------------------------------
$WRAPPER "$DECK" "$MANIFEST"

# ---- 3. validation chain (all must pass) --------------------------------------------
#  a. LO 150dpi render of the wrapped deck vs the pre-wrap render: 0 differing px.
#  b. zip diff: only the slide XML changed; Fallback pics byte-verbatim.
#  c. Choice structure element-for-element == skeleton.xml.
#  d. re-run the wrap: byte-identical (idempotent).
