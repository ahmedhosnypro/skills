#!/usr/bin/env bash
# Pattern: judge-invocation
# The blocking visual-judge comparison: full command shape, wall budgets, retry
# law. Adapt the paths/ids per project; the -p template must come VERBATIM from
# the project's worker-instructions file — never hand-edit it per attempt.
#
# LAWS:
# - WALL BUDGETS: outer wrapper 1700s -> vision-gate 1650s -> call --timeout 600
#   with --thinking high --max-tokens 65536. The gate retries internally; the
#   outer wall must exceed ~2x the per-call wall or it kills a call mid-retry
#   bodyless (measured).
# - DEGENERATE GARBAGE = FAIL: a word-salad / looping / verdict-less body has NO
#   evidentiary value. Re-invoke with identical parameters, new attempt number,
#   up to 3 garbage retries per attempt; 6 attempts per slide, then park for
#   manual review. NEVER certify from a degenerate body.
# - MEASURED-FACTS-IN-CONTEXT: when a coherent FAIL contradicts pixel forensics,
#   retry carrying the measured facts as objective ground truth in the
#   --view/--capture context fields (phrased as facts about the ORIGINAL, e.g.
#   "faint low-contrast ink in the original is real ink, not noise") — never
#   edit the mandatory -p template.
# - A verdict comes ONLY from a real comparison winner body ending in
#   "FINAL VERDICT: PASS or FAIL". Probe first with a cheap read to confirm the
#   window is healthy before spending the wide-wall call.
set -euo pipefail

# ---- parameters (adapt per project) -------------------------------------------
PROJECT=/path/to/project
RENDER=$PROJECT/out/render_K.png          # your 150dpi render
ORIGINAL=$PROJECT/original_frame.jpg      # the original lecture frame
TRANSCRIPT=$PROJECT/out/judge_attempt_K.txt
TEMPLATE=$PROJECT/judge_template.txt      # extracted VERBATIM from worker instructions
VIEW="Slide NNN recreation — fidelity check vs original lecture frame"
CAPTURE="IMG1=150dpi PNG render of a 13.33x7.5in PPTX; IMG2=original lecture frame"

# ---- the judge call (through the project's concurrency gate) --------------------
timeout 1700 "$PROJECT/vision_gate.sh" timeout 1650 python3 \
  "$PROJECT/analyze_image.py" comparison \
  "$RENDER" "$ORIGINAL" \
  --view "$VIEW" \
  --capture "$CAPTURE" \
  --thinking high --max-tokens 65536 \
  --timeout 600 --rounds 1 --tries 1 \
  --transcript "$TRANSCRIPT" \
  -p "$(cat "$TEMPLATE")"

# ---- verdict handling -----------------------------------------------------------
# grep "FINAL VERDICT" "$TRANSCRIPT"
#   PASS from a coherent winner body -> record it; done.
#   Degenerate body -> bank it, retry ONCE per the garbage law (new attempt no.).
#   Coherent FAIL -> PIL-verify each BLOCKER/MAJOR against the original BEFORE
#   rebuilding; disproven claims go into --view as measured facts on the retry.
